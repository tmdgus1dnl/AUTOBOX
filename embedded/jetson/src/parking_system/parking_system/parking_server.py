import time
import math
import numpy as np
import cv2
import cv2.aruco as aruco

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.executors import MultiThreadedExecutor


from geometry_msgs.msg import Twist
from custom_interfaces.action import Parking
import parking_system.stanley_control as sc



import threading
from parking_system.rc_cam_lib import RC_Cam


class ParkingActionServer(Node):

    def __init__(self):
        super().__init__('parking_server_node')

        # ----------------------------------------
        # 1. 통신 설정 (Action Server & CMD Publisher)
        # ----------------------------------------
        self._action_server = ActionServer(
            self,
            Parking,
            'parking_action',
            self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback
        )

        # [NEW] 모터 제어 대신 cmd_vel_parking 토픽 발행
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel_parking', 10)

        # ----------------------------------------
        # 2. 파라미터 설정
        # ----------------------------------------
        self.WHEEL_BASE = 0.1375
        self.MAX_STEER = np.radians(20.0)
        
        # 마커 설정
        self.MARKER_SIZE = 0.10
        self.MARKER_GAP = 0.155
        
        # 제어 파라미터
        self.STOP_DISTANCE = 0.68
        self.SLOW_DISTANCE = 1.2
        self.FORWARD_DISTANCE = 1.1
        self.FAST_SPEED = -0.15
        self.SLOW_SPEED = -0.1

        # ----------------------------------------
        # 3. 카메라 & 스레드 설정 
        # ----------------------------------------

        self.rc_cam = RC_Cam()

        # 스레드 제어 변수
        self.running = True
        self.latest_frame = None        # 메인 로직과 공유할 프레임
        self.frame_lock = threading.Lock() # 동시 접근 방지
        self.streaming_mode = 'FRONT'   # 기본값: 전방 카메라 (주행 모드)

        # 백그라운드 스트리밍 스레드 시작
        self.stream_thread = threading.Thread(target=self.thread_cam_loop)
        self.stream_thread.daemon = True 
        self.stream_thread.start()
        

        # 아루코마커 설정
        #self.cam_matrix = np.array([[1155, 0, 640], [0, 1155, 360], [0, 0, 1]], dtype=float)
        self.cam_matrix = np.array([[771, 0, 320], [0, 771, 240], [0, 0, 1]], dtype=float)
        self.dist_coeffs = np.zeros(5)

        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        self.parameters = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(self.aruco_dict, self.parameters)


        
        # ----------------------------------------
        # 4. 상태 변수
        # ----------------------------------------
        self.state = sc.State(x=0.0, y=0.0, yaw=0.0, v=0.0)
        self.LATERAL_TOLERANCE = 0.03
        self.HEADING_TOLERANCE = np.radians(5.0)
        self.correction_mode = False

        self.get_logger().info("Parking Action Server Ready (Publishing to /cmd_vel_parking)")


    def thread_cam_loop(self):
        """
        이 함수는 계속 돌면서 현재 모드(FRONT/REAR)에 맞는 영상을 
        관제실로 쏘고(Stream), 최신 프레임을 저장합니다.
        """
        while self.running and rclpy.ok():
            # 1. 모드에 따른 카메라 번호 결정 (0:후방, 1:전방 가정)
            if self.streaming_mode == 'FRONT':
                target_idx = 0
            else:
                target_idx = 2
            
            # 2. 카메라 전환 (내부적으로 알아서 끄고 켬)
            self.rc_cam.switch_camera(target_idx)
            
            # 3. 프레임 읽기 (인자 없이 호출)
            ret, frame = self.rc_cam.get_frame()
            
            if ret:
                # 4. GStreamer 송출 (관제실용)
                self.rc_cam.stream()
                
                # 5. 주차 로직용 프레임 공유 (Lock 사용)
                with self.frame_lock:
                    self.latest_frame = frame.copy()
            else:
                # 카메라 전환 시 잠시 딜레이가 생길 수 있음
                time.sleep(0.01)

            # 과부하 방지
            time.sleep(0.01)

    # --- Action Callbacks ---

    def goal_callback(self, goal_request):
        self.get_logger().info('Received Goal Request')
        if goal_request.start_parking:
            return GoalResponse.ACCEPT
        return GoalResponse.REJECT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Received Cancel Request')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing Parking Sequence...')
        
        self.streaming_mode = 'REAR'
        self.get_logger().info('Switched to REAR Camera')
        time.sleep(0.5)
        feedback_msg = Parking.Feedback()
        result = Parking.Result()
        parking_complete = False

        goal = goal_handle.request
        
        # --- [수정 1] 상태 변수 초기화 ---
        # 이전 주행의 데이터가 남아있지 않도록 초기화합니다.
        self.state = sc.State(x=0.0, y=0.0, yaw=0.0, v=0.0)
        self.correction_mode = False
        
        # --- [수정 2] 카메라 버퍼 비우기 (핵심) ---
        # OpenCV 버퍼에 남아있는 '과거 프레임(주차된 상태)'을 강제로 읽어서 버립니다.
        # 이렇게 해야 현재의 실제 위치를 바로 인식할 수 있습니다.
        

        # 파라미터 업데이트 (기존 코드 유지)
        if goal.stop_distance > 0.0:
            self.STOP_DISTANCE = goal.stop_distance
            self.get_logger().info(f"Updated STOP_DISTANCE: {self.STOP_DISTANCE}m")
            
        if goal.slow_distance > 0.0:
            self.SLOW_DISTANCE = goal.slow_distance
            self.get_logger().info(f"Updated SLOW_DISTANCE: {self.SLOW_DISTANCE}m")
        if goal.forward_distance > 0.0:
            self.FORWARD_DISTANCE = goal.forward_distance
            self.get_logger().info(f"Updated FORWARD_DISTANCE: {self.FORWARD_DISTANCE}m")

        try:
            while rclpy.ok() and not parking_complete:
                # 1. 취소 요청 확인
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    self.stop_car()
                    self.get_logger().info('Parking Canceled')
                    self.streaming_mode = 'FRONT'
                    self.get_logger().info('Parking Canceled. Back to FRONT Camera')
                    return result
                
                    

                # 2. 영상 처리
                frame = None
                with self.frame_lock:
                    if self.latest_frame is not None:
                        frame = self.latest_frame.copy()
                
                if frame is None:
                    continue

                
                # ... (이하 기존 로직과 동일) ...
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                corners, ids, rejected = self.detector.detectMarkers(gray)
                
                # ... 생략 ...

                detected = False
                control_steer = 0.0
                control_speed = 0.0
                
                if ids is not None:
                    poses_x, poses_y, poses_yaw = [], [], []
                    ids_flat = ids.flatten()
                    
                    for i, m_id in enumerate(ids_flat):
                        if m_id in [0, 1]:
                            obj_pts = np.array([[-self.MARKER_SIZE/2, self.MARKER_SIZE/2, 0],
                                                [self.MARKER_SIZE/2, self.MARKER_SIZE/2, 0],
                                                [self.MARKER_SIZE/2, -self.MARKER_SIZE/2, 0],
                                                [-self.MARKER_SIZE/2, -self.MARKER_SIZE/2, 0]], dtype=np.float32)
                            
                            _, rvec, tvec = cv2.solvePnP(obj_pts, corners[i][0], self.cam_matrix, self.dist_coeffs)
                            px, py, pyaw = self.get_pose_from_marker(rvec, tvec, m_id)
                            poses_x.append(px)
                            poses_y.append(py)
                            poses_yaw.append(pyaw)

                    if poses_x:
                        detected = True
                        self.state.x = np.mean(poses_x)
                        self.state.y = np.mean(poses_y)
                        self.state.yaw = np.mean(poses_yaw)

                        # (A) 가상 경로 설정
                        if self.state.y > 0:
                            path_y = np.arange(self.state.y, -0.2, -0.05)
                            path_x = np.zeros_like(path_y)
                            path_yaw = np.zeros_like(path_y)
                        else:
                            path_y = np.array([0.0])
                            path_x = np.array([0.0])
                            path_yaw = np.array([0.0])

                        dist = self.state.y
                        current_gear = -1
                        
                        feedback_msg.distance = float(dist)
                        goal_handle.publish_feedback(feedback_msg)

                        # (B) 상태 결정
                        if self.correction_mode:
                            if dist > self.FORWARD_DISTANCE:
                                self.correction_mode = False
                                control_speed = 0.0
                            else:
                                control_speed = 0.15
                                current_gear = 1
                        
                        elif dist < self.STOP_DISTANCE:
                            is_lat_ok = abs(self.state.x) < self.LATERAL_TOLERANCE
                            is_head_ok = abs(self.state.yaw) < self.HEADING_TOLERANCE
                            
                            if is_lat_ok and is_head_ok:
                                control_speed = 0.0
                                parking_complete = True
                                self.get_logger().info("PARKING SUCCESS!")
                            else:
                                self.correction_mode = True
                                control_speed = 0.0
                                self.get_logger().warn("Retry needed")

                        elif dist < self.SLOW_DISTANCE:
                            control_speed = self.SLOW_SPEED
                        else:
                            control_speed = self.FAST_SPEED

                        # (C) Stanley Control
                        if control_speed != 0.0:
                            self.state.v = control_speed
                            delta, _ = sc.stanley_control(
                                self.state, path_x, path_y, path_yaw, 0, gear=current_gear
                            )
                            if current_gear == 1:
                                delta = -delta
                            control_steer = delta
                        else:
                            control_steer = 0.0
                        
                        # [NEW] Twist 메시지 발행
                        vel_w = (control_speed / self.WHEEL_BASE)*math.tan(-control_steer)
                        self.publish_cmd_vel(control_speed, vel_w)

                if not detected:
                    self.stop_car()

                time.sleep(0.05)

        except Exception as e:
            self.get_logger().error(f"Error: {e}")
            self.stop_car()
            self.streaming_mode = 'FRONT'
            goal_handle.abort()
            result.success = False
            return result

        self.stop_car()
        self.get_logger().info("Parking Complete. Back to FRONT Camera")
        self.streaming_mode = 'FRONT'
        
        if parking_complete:
            goal_handle.succeed()
            result.success = True
            result.message = "Parking Complete"
        
        return result

    # --- Helper Functions ---
    def publish_cmd_vel(self, speed, steer):
        """속도와 조향각을 Twist 메시지로 발행"""
        msg = Twist()
        msg.linear.x = float(speed)
        msg.angular.z = float(steer) # 받는 쪽에서 이를 조향각(rad)으로 해석해야 함
        self.cmd_vel_pub.publish(msg)

    def stop_car(self):
        """정지 명령 발행"""
        self.publish_cmd_vel(0.0, 0.0)

    def get_pose_from_marker(self, rvec, tvec, marker_id):
        # (기존 코드와 동일)
        R, _ = cv2.Rodrigues(rvec)
        cam_pos = -np.dot(R.T, tvec)
        x = cam_pos[0][0]
        z = cam_pos[2][0]
        cam_z = R.T[:, 2]
        yaw = math.atan2(cam_z[0], cam_z[2]) 
        yaw = self.normalize_angle(yaw + math.pi)
        offset = -self.MARKER_GAP/2.0 if marker_id == 0 else self.MARKER_GAP/2.0
        return x + offset, z, yaw

    def normalize_angle(self, angle):
        while angle > math.pi: angle -= 2.0 * math.pi
        while angle < -math.pi: angle += 2.0 * math.pi
        return angle

def main(args=None):
    rclpy.init(args=args)
    parking_server = ParkingActionServer()
    executor = MultiThreadedExecutor()
    rclpy.spin(parking_server, executor=executor)
    parking_server.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
