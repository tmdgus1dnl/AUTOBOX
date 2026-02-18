import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from tf2_ros import Buffer, TransformListener
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException

class RobotPosePublisher(Node):
    def __init__(self):
        super().__init__('robot_pose_publisher')
        
        # 1. 퍼블리셔 생성 (토픽명: /robot_pose)
        self.publisher_ = self.create_publisher(PoseStamped, 'robot_pose', 10)
        
        # 2. TF 리스너 설정
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # 3. 20Hz(0.05초)마다 실행되는 타이머
        self.timer = self.create_timer(0.05, self.timer_callback)

    def timer_callback(self):
        try:
            # 'map' 기준 'base_link'의 위치를 조회
            # (Time(0)은 가장 최신 데이터를 의미)
            t = self.tf_buffer.lookup_transform(
                'map', 
                'base_link', 
                rclpy.time.Time())

            # PoseStamped 메시지로 변환
            msg = PoseStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'map'
            
            msg.pose.position.x = t.transform.translation.x
            msg.pose.position.y = t.transform.translation.y
            msg.pose.position.z = t.transform.translation.z
            msg.pose.orientation = t.transform.rotation

            # 발행!
            self.publisher_.publish(msg)

        except (LookupException, ConnectivityException, ExtrapolationException):
            # 아직 맵이나 TF가 준비 안 됐으면 무시
            pass

def main(args=None):
    rclpy.init(args=args)
    node = RobotPosePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
