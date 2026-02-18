#ifndef MISSION_MANAGER_HPP_
#define MISSION_MANAGER_HPP_

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "nav2_msgs/action/navigate_to_pose.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "geometry_msgs/msg/twist.hpp" 
#include "std_msgs/msg/bool.hpp"
#include "std_msgs/msg/string.hpp"
#include "std_msgs/msg/float64.hpp"
#include "std_msgs/msg/int32.hpp"

// [NEW] Pose Estimate 및 TF 관련 헤더
#include "geometry_msgs/msg/pose_with_covariance_stamped.hpp"
#include "tf2_ros/transform_listener.h"
#include "tf2_ros/buffer.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"
#include <cmath>

#include "custom_interfaces/action/parking.hpp" 

enum class MissionState {
  START,
  IDLE,
  WAITING_FOR_LOADING,
  PRE_NAV_TO_TARGET, 
  NAV_TO_TARGET,
  PARKING_AT_TARGET,
  UNLOADING,
  PRE_NAV_TO_HOME,   
  NAV_TO_HOME,
  PARKING_AT_HOME
};

class MissionManager : public rclcpp::Node {
public:
  using NavigateToPose = nav2_msgs::action::NavigateToPose;
  using GoalHandleNav = rclcpp_action::ClientGoalHandle<NavigateToPose>;
  using ParkingAction = custom_interfaces::action::Parking;
  using GoalHandleParking = rclcpp_action::ClientGoalHandle<ParkingAction>;

  MissionManager();

private:
  void state_machine_loop();

  void rpi_command_callback(const geometry_msgs::msg::PoseStamped::SharedPtr msg);
  void rpi_call_callback(const std_msgs::msg::Bool::SharedPtr msg);

  void send_nav2_goal(const geometry_msgs::msg::PoseStamped& pose);
  void nav2_result_callback(const GoalHandleNav::WrappedResult & result);
  void nav2_feedback_callback(
    rclcpp_action::ClientGoalHandle<nav2_msgs::action::NavigateToPose>::SharedPtr,
    const std::shared_ptr<const nav2_msgs::action::NavigateToPose::Feedback> feedback);
  void send_parking_goal();
  void parking_result_callback(const GoalHandleParking::WrappedResult & result);

  // [NEW] 위치 보정 Helper 함수
  void save_parked_pose_from_tf(); // 주차 완료 시 호출 (현재 TF 저장)
  void publish_initial_pose();     // 출발 전 호출 (/initialpose 발행)

  rclcpp::TimerBase::SharedPtr timer_;

  rclcpp_action::Client<NavigateToPose>::SharedPtr nav_client_;
  rclcpp_action::Client<ParkingAction>::SharedPtr parking_client_;

  rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr rpi_sub_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr rpi_call_sub_;
  
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr rpi_status_pub_;
  rclcpp::Publisher<std_msgs::msg::Float64>::SharedPtr actuator_pub_; 
  rclcpp::Publisher<std_msgs::msg::Float64>::SharedPtr remaindist_pub_;
  rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr remaintime_pub_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_pre_pub_;

  // [NEW] 초기 위치(Pose Estimate) 발행용 Publisher
  rclcpp::Publisher<geometry_msgs::msg::PoseWithCovarianceStamped>::SharedPtr initial_pose_pub_;

  // [NEW] TF Listener (자신의 위치 파악용)
  std::shared_ptr<tf2_ros::Buffer> tf_buffer_;
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_;

  MissionState current_state_;
  geometry_msgs::msg::PoseStamped target_pose_;
  geometry_msgs::msg::PoseStamped home_pose_;
  
  // [NEW] 마지막으로 주차 완료했을 때의 로봇 위치 저장
  geometry_msgs::msg::PoseStamped last_parked_pose_;

  bool nav2_goal_reached_ = false;

  int unloading_step_ = 0;
  rclcpp::Time unloading_start_time_;
  
  int pre_move_step_ = 0;
  bool start_flag = true;
  rclcpp::Time pre_move_start_time_;
};

#endif // MISSION_MANAGER_HPP_