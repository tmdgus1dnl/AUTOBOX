import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import String, Bool, Float64, Int32
import paho.mqtt.client as mqtt
import json
import math
import yaml

class SmartMqttBridge(Node):
    def __init__(self):
        super().__init__('smart_mqtt_bridge')

        # 파라미터
        self.declare_parameter('mqtt_broker_ip', '')
        self.declare_parameter('mqtt_port', 1883)
        self.declare_parameter('topic_cmd_sub', 'factory_msg/rc1/command')
        self.declare_parameter('topic_status_pub', 'edge_msg/rc1/state')
        self.declare_parameter('topic_rpi_control', 'edge_msg/rc1/command') 
        self.declare_parameter('waypoint_file_path', '/home/jetson/ros2_ws/src/mqtt_bridge_pkg/config/waypoints.yaml')
        self.broker_ip = self.get_parameter('mqtt_broker_ip').value
        self.mqtt_port = self.get_parameter('mqtt_port').value
        self.topic_sub = self.get_parameter('topic_cmd_sub').value
        self.topic_pub = self.get_parameter('topic_status_pub').value
        self.topic_rpi_control = self.get_parameter('topic_rpi_control').value
        
        waypoint_file = self.get_parameter('waypoint_file_path').value

        # Waypoint 로드
        self.waypoints = {}
        try:
            if waypoint_file:
                with open(waypoint_file, 'r') as f:
                    self.waypoints = yaml.safe_load(f)
        except Exception as e:
            self.get_logger().error(f"Failed to load waypoints: {e}")

        # --- ROS 2 통신 ---
        # 1. 목적지 전송 (적재 완료 후)
        self.mission_start_pub = self.create_publisher(PoseStamped, 'mission/start_delivery', 10)
        
        # 2. [NEW] 로봇 호출 신호 전송 ("COME_HERE" 수신 시)
        self.call_robot_pub = self.create_publisher(Bool, 'mission/call_robot', 10)

        # 3. 상태 구독
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.create_subscription(String, 'mission/status', self.state_callback, 10)
        self.create_subscription(PoseStamped, '/robot_pose', self.pose_callback, 10)
        self.create_subscription(String, '/path_json', self.path_callback,10)
        self.create_subscription(Float64, '/remain_dist', self.remain_dist_callback,10)
        self.create_subscription(Int32, '/remain_time', self.remain_time_callback,10)

        # 상태 변수
        self.current_speed = 0.0
        self.mission_state = "IDLE"
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_theta = 0.0
        self.current_path = ''
        self.remain_dist = 0.0
        self.remain_time = 0
        
        # 중복 전송 방지 플래그
        self.arrived_msg_sent = False 

        # --- MQTT 연결 ---
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "JetsonBridge")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_ip, self.mqtt_port, 60)
        self.client.loop_start()

        self.create_timer(0.5, self.publish_robot_status)

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe(self.topic_sub)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # [CASE 1] 호출 명령 (COME_HERE)
            if "cmd" in payload and payload["cmd"] == "COME_HERE":
                # 로봇에게 호출 신호 보냄 (Mission Manager가 IDLE일 때만 반응함)
                self.call_robot_pub.publish(Bool(data=True))
                # self.get_logger().info("Received COME_HERE -> Calling Robot")

            # [CASE 2] 목적지 명령 (target) - 적재 완료 후 옴
            elif "target" in payload:
                target_name = payload.get("target")
                if target_name in self.waypoints:
                    data = self.waypoints[target_name]
                    ros_msg = PoseStamped()
                    ros_msg.header.frame_id = "map"
                    ros_msg.header.stamp = self.get_clock().now().to_msg()
                    ros_msg.pose.position.x = float(data[0])
                    ros_msg.pose.position.y = float(data[1])
                    theta = float(data[2])
                    ros_msg.pose.orientation.z = math.sin(theta / 2.0)
                    ros_msg.pose.orientation.w = math.cos(theta / 2.0)

                    self.mission_start_pub.publish(ros_msg)
                    self.get_logger().info(f"Loading Complete. Target '{target_name}' sent.")
                    
                    # 다음 사이클을 위해 플래그 초기화
                    self.arrived_msg_sent = False 

        except Exception as e:
            self.get_logger().error(f"MQTT Parsing Error: {e}")

    def state_callback(self, msg):
        self.mission_state = msg.data
        
        # [NEW] 로봇이 적재 대기 상태("READY_TO_LOAD")가 되면 RPi에 "ARRIVED" 전송
        if self.mission_state == "READY_TO_LOAD" and not self.arrived_msg_sent:
            
            # RPi로 보낼 메시지 (도착했으니 적재 시작해라)
            resp_payload = {
                "device_id": "rc1",
                "cmd": "ready" 
            }
            self.client.publish(self.topic_rpi_control, json.dumps(resp_payload))
            resp_payload = {
                "device_id": "rc1",
                "cmd": "ARRIVED" 
            }
            self.client.publish(self.topic_rpi_control, json.dumps(resp_payload))
            self.get_logger().info("Robot Arrived. Sent 'ARRIVED' signal to RPi.")
            
            self.arrived_msg_sent = True # 중복 전송 방지

    def odom_callback(self, msg):
        self.current_speed = msg.twist.twist.linear.x
    def pose_callback(self, msg):
        self.current_x = msg.pose.position.x
        self.current_y = msg.pose.position.y
        rx = msg.pose.orientation.x
        ry = msg.pose.orientation.y
        z = msg.pose.orientation.z
        w = msg.pose.orientation.w
        
        siny_cosp = 2 * (w * z + rx * ry)
        cosy_cosp = 1 - 2 * (ry * ry + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        self.current_theta = yaw
    def path_callback(self,msg):
        self.current_path = msg.data
    def remain_dist_callback(self, msg):
        self.remain_dist = msg.data
    def remain_time_callback(self, msg):
        self.remain_time = msg.data

    def publish_robot_status(self):
        status_data = {
            "device_id": "rc1",
            "speed": round(self.current_speed, 4),
            "state": self.mission_state,
            "x": round(self.current_x, 4),
            "y": round(self.current_y, 4),
            "theta": round(self.current_theta, 4),
            "path": self.current_path,
            "remain_dist": self.remain_dist,
            "remain_time": self.remain_time,
        }
        self.client.publish(self.topic_pub, json.dumps(status_data))

def main(args=None):
    rclpy.init(args=args)
    node = SmartMqttBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()