from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration # [수정] 추가
from launch.conditions import IfCondition # [수정] 추가
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    # [추가 1] 앱 모드 스위치 (기본값 True)
    # 실행 시 'ros2 launch ... app:=False'라고 하면 미션 매니저는 끄고 로봇만 켭니다.

    app_arg = DeclareLaunchArgument(
        'app', default_value='False',
        description='Run Mission Manager & MQTT Bridge'
    )
    
    twist_mux_config = os.path.join(
        get_package_share_directory('parking_system'),
        'config',
        'twist_mux.yaml'
    )

    # --- YDLIDAR launch ---
    ydlidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ydlidar_ros2_driver'),
                'launch',
                'ydlidar_launch_view.py'   # 실전에서는 view 제거
            )
        )
    )

    # --- RF2O launch include ---
    rf2o_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('rf2o_laser_odometry'),
                'launch',
                'rf2o_laser_odometry.launch.py'
            )
        )
    )



    # --- Ackermann Wheel Odometry ---
    ackermann_odom = Node(
        package='cpp_ackermann_odom',
        executable='ackermann_odom_node',
        name='ackermann_odom_node',
        output='screen',
    )

    mpu_6050 = Node(
        package='mpu6050_cpp_driver',
        executable='mpu6050_node',
        name='mpu6050_node',
        output='screen'
    )

    madgwick = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter_madgwick_node',
        output='screen',
        parameters=[{
            'use_mag': False,          # MPU6050은 지자기 센서가 없으므로 False 필수!
            'publish_tf': False,       # 나중에 EKF가 tf를 발행할 것이므로 여기선 False
            'world_frame': 'enu'       # 방향 기준 (East-North-Up)
        }]
    )

    imu_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_link_to_imu',
        arguments=[
            '0.0', '0.0', '0.0',  # X, Y, Z 위치 (미터 단위) - 센서가 로봇 중앙에 있다면 0,0,0
            '0.0', '0.0', '0.0',  # Yaw, Pitch, Roll 회전 (라디안 단위) - 이 값을 수정합니다!
            'base_link',          # 부모 좌표계 (RC카 중심)
            'imu_link'            # 자식 좌표계 (센서)
        ]
    )
    # --- EKF ---
    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[
            os.path.join(
                get_package_share_directory('robot_localization'),
                'params',
                'ekf.yaml'
            )
        ],
        remappings=[
            ('/odometry/filtered', '/odom')
        ]
    )

    # --- fake odom ---
    #fake_odom = Node(
    #    package='fake_odom',
    #    executable='fake_odom_node',
    #    name='fake_odom',
    #    output='screen'
    #)

    # --- SLAM Toolbox only ---
    slam_toolbox = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('slam_toolbox'),
                'launch',
                'online_async_launch.py'
            )
        ),
        launch_arguments={
            'use_sim_time': 'False',
        # 'slam_params_file': '/home/jetson/ros2_ws/src/rc_car_bringup/config/slam_toolbox.yaml',
        }.items()
    )

    # --- Nav2 bringup (SLAM mode) ---
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('nav2_bringup'),
                'launch',
                'bringup_launch.py'
            )
        ),
        launch_arguments={
            'slam': 'True',
            'use_sim_time': 'False',
            'autostart': 'True',
            'use_composition': 'False',
            'map': '/home/jetson/maps/dummy.yaml',
            'params_file': '/opt/ros/humble/share/nav2_bringup/params/nav2_params.yaml',
        }.items()
    )

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

# -------------------------------------------------------------
    # [신규 추가] 1. PCA Drive Node (하드웨어 제어)
    # -------------------------------------------------------------
    pca_drive_node = Node(
        package='rc_car_bot',       # 아까 만든 패키지 이름
        executable='pca_drive',     # CMakeLists.txt에 등록한 실행 파일명
        name='pca_drive_node',
        output='screen',
        parameters=[{
            'i2c_dev': '/dev/i2c-7',       # Jetson Nano 기본값 (라즈베리파이는 /dev/i2c-1 확인 필수!)
            'addr_servo': 0x60,
            'addr_motor': 0x40,
            'motor_base_channel': 0,
            'servo_channel': 0,
            'servo_center_deg': 100,        # 차량에 맞게 튜닝 (직진 각도)
            'max_linear': 0.5,             # 최대 속도 제한
            'max_angular': 1.0,            # 최대 조향각 제한
        }]
    )
    
    # -------------------------------------------------------------
    # [신규 추가] 2. Keyboard Latch Node (키보드 제어)
    # -------------------------------------------------------------
    # 주의: 이 런치 파일을 실행한 터미널에서 키 입력을 받습니다.
    keyboard_latch_node = Node(
        package='rc_car_bot',
        executable='keyboard_latch',
        name='keyboard_latch_node',
        output='screen',
        prefix='xterm -e', # (선택사항) 키보드 입력을 위해 별도 터미널 창을 띄우고 싶다면 사용 (xterm 설치 필요)
                           # 그냥 현재 터미널을 쓰려면 이 줄(prefix)을 지우세요.
        parameters=[{
            'publish_hz': 20.0,
            'speed_max': 0.5,
            'steer_max': 1.0
        }]
    )
    # -------------------------------------------------------------
    # [추가 2] Application Layer (MQTT Bridge & Mission Manager)
    # -------------------------------------------------------------

    # 1. MQTT Bridge Launch 포함 (params.yaml도 여기서 자동 로드됨)
    mqtt_bridge_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('mqtt_bridge_pkg'),
                'launch',
                'bridge_launch.py'
            )
        ),
        condition=IfCondition(LaunchConfiguration('app')) # app:=True일 때만 실행
    )

    # 2. Mission Manager Node (C++)
    mission_manager_node = Node(
        package='mission_manager',
        executable='mission_manager_node',
        name='mission_manager',
        output='screen',
        condition=IfCondition(LaunchConfiguration('app')) # app:=True일 때만 실행
    )
    
    # 2. Twist Mux 노드 정의
    twist_mux_node = Node(
        package='twist_mux',
        executable='twist_mux',
        name='twist_mux',
        output='screen',
        parameters=[twist_mux_config],
        remappings=[
            ('cmd_vel_out', '/cmd_vel_final') # Mux가 내보낼 최종 토픽 이름
        ]
    )
    parking_node = Node(
        package='parking_system',      # 패키지 이름
        executable='parking_server',   # setup.py의 entry_points 이름
        name='parking_server',         # 노드 이름 (원하는 대로)
        output='screen'
        # remappings는 필요 없습니다. 
        # (코드 내부에서 이미 /cmd_vel_parking 으로 발행하도록 설정했기 때문)
    )

    return LaunchDescription([
        #app_arg,            # [추가] 아규먼트 등록
        ydlidar_launch,
        rf2o_launch,
        #ackermann_odom,
        #mpu_6050,
        #madgwick,
        #imu_tf,
        ekf,
        #rc_car,
        slam_toolbox,
        pca_drive_node,
        keyboard_latch_node,
        #nav2,
        # [추가] 앱 계층 실행
        #mqtt_bridge_launch,
        #mission_manager_node
        twist_mux_node,    # 추가된 Twist Mux
        parking_node,
    ])
