cmake_minimum_required(VERSION 3.8)
project(custom_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
# 1. 의존성 패키지 찾기
find_package(rosidl_default_generators REQUIRED)
find_package(action_msgs REQUIRED)

# 2. 인터페이스 생성 설정
rosidl_generate_interfaces(${PROJECT_NAME}
  "action/Parking.action"
  DEPENDENCIES action_msgs
)

# 3. 내보내기 설정
ament_export_dependencies(rosidl_default_runtime)

ament_package()