cmake_minimum_required(VERSION 3.8)
project(rc_car_bot)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 의존성 패키지 찾기
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)

# 1. 키보드 제어 노드 빌드 설정
add_executable(keyboard_latch src/keyboard_latch_node.cpp)
ament_target_dependencies(keyboard_latch rclcpp geometry_msgs)

# 2. PCA9685 구동 노드 빌드 설정
add_executable(pca_drive src/pca_drive_node.cpp)
ament_target_dependencies(pca_drive rclcpp geometry_msgs)

# 실행 파일 설치 경로 설정 (이게 있어야 ros2 run으로 실행 가능)
install(TARGETS
  keyboard_latch
  pca_drive
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
