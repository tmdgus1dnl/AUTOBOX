import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from nav_msgs.msg import Path
from std_msgs.msg import String
import json

class PathPublisher(Node):
    def __init__(self):
        super().__init__('path_publisher')

        # 1. Nav2의 경로(/plan) 구독
        # [중요] Nav2의 /plan 토픽은 'Transient Local' QoS를 씁니다.
        # 이걸 맞춰주지 않으면 데이터를 하나도 못 받습니다!
        qos_profile = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.VOLATILE,
            reliability=ReliabilityPolicy.RELIABLE
        )
        
        self.sub_path = self.create_subscription(
            Path,
            '/plan',  # Nav2가 발행하는 글로벌 경로 토픽
            self.path_callback,
            qos_profile
        )
        
        # 2. JSON 문자열로 변환해서 내보낼 퍼블리셔
        self.create_subscription(String, 'mission/status', self.state_callback, 10)
        self.pub_json = self.create_publisher(String, '/path_json', 10)
        
        self.get_logger().info("Path Publisher Node Started. Waiting for /plan...")

    def path_callback(self, msg):
        # msg.poses 안에 수백 개의 좌표가 들어있음
        path_list = []

        # 데이터 경량화를 위해 필요한 것만 뽑음
        for pose_stamped in msg.poses:
            point = {
                'x': round(pose_stamped.pose.position.x, 3), # 소수점 3자리로 줄임
                'y': round(pose_stamped.pose.position.y, 3)
            }
            path_list.append(point)

        # 리스트를 JSON 문자열로 변환
        json_str = json.dumps(path_list)

        # ROS String 메시지에 담아서 발행
        ros_msg = String()
        ros_msg.data = json_str
        self.pub_json.publish(ros_msg)
        
        # 로그 (너무 자주 뜨면 주석 처리)
        # self.get_logger().info(f"Published path with {len(path_list)} points")
        
    def state_callback(self, msg):
        ros_msg = String()
        ros_msg.data = ""
        if msg.data in ["IDLE", "UNLOADING"]:
          self.pub_json.publish(ros_msg)
        

def main(args=None):
    rclpy.init(args=args)
    node = PathPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
