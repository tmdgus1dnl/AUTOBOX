cmake_minimum_required(VERSION 3.8)
project(fake_odom)

# 컴파일 옵션 (경고 표시)
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ---- 의존성 패키지 찾기 ----
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(geometry_msgs REQUIRED)

# ---- 실행 파일 추가 ----
add_executable(fake_odom_node
  src/fake_odom_node.cpp
)

# ---- 실행 파일에 의존성 연결 ----
ament_target_dependencies(fake_odom_node
  rclcpp
  nav_msgs
  tf2
  tf2_ros
  geometry_msgs
)

# ---- 설치 규칙 ----
install(TARGETS
  fake_odom_node
  DESTINATION lib/${PROJECT_NAME}
)

# ---- 패키지 선언 ----
ament_package()
