cmake_minimum_required(VERSION 3.8)
project(mission_manager)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 1. 의존성 패키지 찾기
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
# ▼▼▼ [필수 추가] 아래 두 줄이 없어서 에러가 난 것입니다! ▼▼▼
find_package(std_msgs REQUIRED)
find_package(custom_interfaces REQUIRED) 

# ==========================================
# ▼▼▼ 빌드 설정 ▼▼▼
# ==========================================

include_directories(include)

# 2. 실행 파일(Executable) 생성
add_executable(mission_manager_node src/mission_manager.cpp)

# 3. 의존성 라이브러리 연결
ament_target_dependencies(mission_manager_node
  rclcpp
  rclcpp_action
  nav2_msgs
  tf2_ros
  tf2_geometry_msgs
  geometry_msgs
  # ▼▼▼ [필수 추가] 여기에도 추가해야 링크가 됩니다! ▼▼▼
  std_msgs
  custom_interfaces
)

# 4. 설치(Install) 설정
install(TARGETS
  mission_manager_node
  DESTINATION lib/${PROJECT_NAME}
)

# include 폴더 설치 (헤더 파일이 있을 경우)
install(DIRECTORY include/
  DESTINATION include
)

# ==========================================
# ▲▲▲ 설정 완료 ▲▲▲
# ==========================================

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()