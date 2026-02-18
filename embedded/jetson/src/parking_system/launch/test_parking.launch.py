import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    
    # 1. 모터 드라이버 (기존 bringup 설정 그대로 가져옴)
    rc_car = Node(
        package='rc_car_driver',
        executable='rc_car_node',
        name='rc_car_node',
        output='screen',
        parameters=[{
            'cmd_vel_topic': '/cmd_vel_final',
            'control_rate': 20.0,
            'cmd_timeout': 0.2,
            'motor_channel': 0,
            'servo_pca_address': 0x60,
            'servo_channel': 0,
            'steer_center_deg': 100.0,
            'wheelbase_m': 0.1375,
            'publish_applied_cmd': True,
            'applied_cmd_topic': '/rc_car/applied_cmd_vel',
            }],
        )

    # 2. 주차 서버
    # 원래는 /cmd_vel_parking을 보내지만, 테스트를 위해 /cmd_vel_final로 리매핑하여 직결합니다.
    parking_node = Node(
        package='parking_system',
        executable='parking_server',
        name='parking_server',
        output='screen',
        remappings=[
            ('/cmd_vel_parking', '/cmd_vel_final') # [중요] Twist Mux 없이 바로 연결
        ]
    )

    return LaunchDescription([
        rc_car,
        parking_node
    ])