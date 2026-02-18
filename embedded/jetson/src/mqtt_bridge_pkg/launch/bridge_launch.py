import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_name = 'mqtt_bridge_pkg'
    
    # 설정 파일 경로 찾기
    config_file = os.path.join(
        get_package_share_directory(pkg_name),
        'config',
        'params.yaml'
    )
    
    waypoint_file = os.path.join(
        get_package_share_directory(pkg_name),
        'config',
        'waypoints.yaml'
    )

    return LaunchDescription([
        Node(
            package=pkg_name,
            executable='mqtt_bridge_node',
            name='smart_mqtt_bridge',
            output='screen',
            parameters=[
                config_file,  # 1. 일반 파라미터 로드
                {'waypoint_file_path': waypoint_file} # 2. 좌표 파일 경로 주입
            ]
        )
    ])
