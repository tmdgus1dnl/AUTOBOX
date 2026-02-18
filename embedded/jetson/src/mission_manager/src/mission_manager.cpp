#include "mission_manager/mission_manager.hpp"

using namespace std::chrono_literals;

MissionManager::MissionManager() : Node("mission_manager_node") {
  current_state_ = MissionState::START;
  nav2_goal_reached_ = false;
  unloading_step_ = 0;
  pre_move_step_ = 0;
  start_flag = false;

  home_pose_.header.frame_id = "map";
  home_pose_.pose.position.x = -0.239495;
  home_pose_.pose.position.y = 0.090556;
  home_pose_.pose.orientation.x = 0.0;
  home_pose_.pose.orientation.y = 0.0;
  home_pose_.pose.orientation.z = sin(0.15/2.0);
  home_pose_.pose.orientation.w = cos(0.15/2.0);
  
  // [기본값 설정] 첫 실행 시 주차 기록이 없으므로 Home 위치를 초기값으로 설정
  last_parked_pose_ = home_pose_;
  last_parked_pose_.pose.position.x = 0.0;

  nav_client_ = rclcpp_action::create_client<NavigateToPose>(this, "navigate_to_pose");
  parking_client_ = rclcpp_action::create_client<ParkingAction>(this, "parking_action");

  rpi_sub_ = this->create_subscription<geometry_msgs::msg::PoseStamped>(
      "mission/start_delivery", 10,
      std::bind(&MissionManager::rpi_command_callback, this, std::placeholders::_1));

  rpi_call_sub_ = this->create_subscription<std_msgs::msg::Bool>(
      "mission/call_robot", 10,
      std::bind(&MissionManager::rpi_call_callback, this, std::placeholders::_1));
  rpi_status_pub_ = this->create_publisher<std_msgs::msg::String>("mission/status", 10);
  actuator_pub_ = this->create_publisher<std_msgs::msg::Float64>("/cmd_vel_act", 10);
  cmd_vel_pre_pub_ = this->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel_pre", 10);
  remaindist_pub_ = this->create_publisher<std_msgs::msg::Float64>("/remain_dist", 10);
  remaintime_pub_ = this->create_publisher<std_msgs::msg::Int32>("/remain_time", 10);
  
  // Pose Estimate Publisher (AMCL QoS에 맞춰 BEST_EFFORT로)
  auto init_qos = rclcpp::QoS(rclcpp::KeepLast(1))
                  .best_effort()
                  .durability_volatile();

  initial_pose_pub_ = this->create_publisher<geometry_msgs::msg::PoseWithCovarianceStamped>("/initialpose", init_qos);
  
  // TF Listener 초기화
  tf_buffer_ = std::make_shared<tf2_ros::Buffer>(this->get_clock());
  tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);
  
  timer_ = this->create_wall_timer(
      100ms, std::bind(&MissionManager::state_machine_loop, this));

  RCLCPP_INFO(this->get_logger(), "Mission Manager Ready.");
}

// [NEW] RPi 호출 콜백
void MissionManager::rpi_call_callback(const std_msgs::msg::Bool::SharedPtr msg) {
    if (msg->data && current_state_ == MissionState::IDLE) {
        RCLCPP_INFO(this->get_logger(), "Call Received! Waiting for loading...");
        
        // IDLE -> 적재 대기 상태로 변경
        current_state_ = MissionState::WAITING_FOR_LOADING;
        
        // 상태 보고 (Bridge가 이걸 보고 RPi에 ARRIVED 전송함)
        std_msgs::msg::String status; 
        status.data = "READY_TO_LOAD"; 
        rpi_status_pub_->publish(status);
    }
}

// [수정됨] 목적지 수신 콜백 (중복 제거 완료)
void MissionManager::rpi_command_callback(const geometry_msgs::msg::PoseStamped::SharedPtr msg) {
  // WAITING_FOR_LOADING 상태일 때만 목적지 명령을 수락
  if (current_state_ == MissionState::WAITING_FOR_LOADING || current_state_ == MissionState::IDLE) {
    RCLCPP_INFO(this->get_logger(), "Loading Complete. Destination Received!");
    target_pose_ = *msg;

    current_state_ = MissionState::PRE_NAV_TO_TARGET;
    pre_move_step_ = 0;
  } else {
    RCLCPP_WARN(this->get_logger(), "Ignored command. Robot is busy.");
  }
}

void MissionManager::state_machine_loop() {
    auto now = this->now();
    switch (current_state_) {
        case MissionState::START:
        {
           std_msgs::msg::Float64 act_msg;
           if (unloading_step_ == 0) {
              act_msg.data = -1.0;
              actuator_pub_->publish(act_msg); 
              RCLCPP_INFO(this->get_logger(), "Unloading Step 1: Forward");
              unloading_start_time_ = now;
              unloading_step_ = 1;
          }
          else if (unloading_step_ == 1) {
              act_msg.data = -1.0;
              actuator_pub_->publish(act_msg); 
              if (now - unloading_start_time_ >= std::chrono::milliseconds(10000)) {
                  act_msg.data = 1.0;
                  actuator_pub_->publish(act_msg); 
                  RCLCPP_INFO(this->get_logger(), "Unloading Step 2: Backward");
                  unloading_start_time_ = now;
                  unloading_step_ = 2;
              }
          }
          else if (unloading_step_ == 2) {
              act_msg.data = 1.0;
              actuator_pub_->publish(act_msg); 
              if (now - unloading_start_time_ >= std::chrono::milliseconds(3000)) {
                  act_msg.data = 0.0;
                  actuator_pub_->publish(act_msg); 
                  RCLCPP_INFO(this->get_logger(), "Unloading Complete.");
                  unloading_start_time_ = now;
                  unloading_step_ = 3; 
              }
          }
          else if (unloading_step_ == 3) {
              act_msg.data = 0.0;
              actuator_pub_->publish(act_msg); 
              if (now - unloading_start_time_ >= std::chrono::milliseconds(500)) {
                  act_msg.data = 0.0;
                  actuator_pub_->publish(act_msg); 
              
                  current_state_ = MissionState::IDLE;
                   
              }
          }
        }
        break;
        
        case MissionState::IDLE:
        {
          std_msgs::msg::String status; status.data = "IDLE";
          rpi_status_pub_->publish(status);
        }
        break;

        case MissionState::WAITING_FOR_LOADING:
        break;

        // =========================================================
        // [CASE] 출발 전 (Target 행)
        // =========================================================
        case MissionState::PRE_NAV_TO_TARGET:
        {
            if (pre_move_step_ == 0) {
                // 1. Pose Estimate (위치 초기화) 수행
                RCLCPP_INFO(this->get_logger(), "Initializing Pose before Move (Target)...");
                publish_initial_pose(); 

                RCLCPP_INFO(this->get_logger(), "Step 1: Forward Push (Target)");
                pre_move_start_time_ = now;
                pre_move_step_ = 1;
                
                std_msgs::msg::String status; status.data = "STARTING_DELIVER";
                rpi_status_pub_->publish(status);
            }
            else if(pre_move_step_ == 1) {
              if (now - pre_move_start_time_ >= std::chrono::milliseconds(500)) {
                  pre_move_step_ = 2;
                  pre_move_start_time_ = now;
              }
            }
            else if (pre_move_step_ == 2) {
                // [수정] 1.5초 동안 명령을 지속적으로 전송 (Watchdog 방지)
                geometry_msgs::msg::Twist msg;
                msg.linear.x = 0.2; 
                cmd_vel_pre_pub_->publish(msg); 

                // 1.5초 후 종료 체크
                if (now - pre_move_start_time_ >= std::chrono::milliseconds(2000)) {
                   geometry_msgs::msg::Twist stop_msg;
                   stop_msg.linear.x = 0.0;
                   cmd_vel_pre_pub_->publish(stop_msg);
                   
                   send_nav2_goal(target_pose_);
                   current_state_ = MissionState::NAV_TO_TARGET;
                   std_msgs::msg::String status; status.data = "DELIVERING";
                   rpi_status_pub_->publish(status);
                }
            }
        }
        break;

        case MissionState::NAV_TO_TARGET:
            if (nav2_goal_reached_) {
                nav2_goal_reached_ = false;
                send_parking_goal();
                current_state_ = MissionState::PARKING_AT_TARGET;
                std_msgs::msg::String status; status.data = "PARKING_AT_TARGET";
                rpi_status_pub_->publish(status);
            }
        break;
        
        case MissionState::PARKING_AT_TARGET: break;

        case MissionState::UNLOADING:
        {
             std_msgs::msg::Float64 act_msg;
             if (unloading_step_ == 0) {
                act_msg.data = 1.0;
                actuator_pub_->publish(act_msg); 
                RCLCPP_INFO(this->get_logger(), "Unloading Step 1: Forward");
                unloading_start_time_ = now;
                unloading_step_ = 1;
                
                std_msgs::msg::String status; status.data = "UNLOADING";
                rpi_status_pub_->publish(status);
            }
            else if (unloading_step_ == 1) {
                act_msg.data = 1.0;
                actuator_pub_->publish(act_msg); 
                if (now - unloading_start_time_ >= std::chrono::milliseconds(10000)) {
                    act_msg.data = -1.0;
                    actuator_pub_->publish(act_msg); 
                    RCLCPP_INFO(this->get_logger(), "Unloading Step 2: Backward");
                    unloading_start_time_ = now;
                    unloading_step_ = 2;
                }
            }
            else if (unloading_step_ == 2) {
                act_msg.data = -1.0;
                actuator_pub_->publish(act_msg); 
                if (now - unloading_start_time_ >= std::chrono::milliseconds(10000)) {
                    act_msg.data = 0.0;
                    actuator_pub_->publish(act_msg); 
                    RCLCPP_INFO(this->get_logger(), "Unloading Complete.");
                    unloading_start_time_ = now;
                    unloading_step_ = 3; 
                }
            }
            else if (unloading_step_ == 3) {
                act_msg.data = 0.0;
                actuator_pub_->publish(act_msg); 
                if (now - unloading_start_time_ >= std::chrono::milliseconds(500)) {
                    act_msg.data = 0.0;
                    actuator_pub_->publish(act_msg); 
                    RCLCPP_INFO(this->get_logger(), "Unloading Complete.");
                    
                    std_msgs::msg::String status; status.data = "STARTING RETURN";
                    rpi_status_pub_->publish(status);
                    current_state_ = MissionState::PRE_NAV_TO_HOME;
                    pre_move_step_ = 0; 
                }
            }
        }
        break;

        // =========================================================
        // [CASE] 복귀 전 (Home 행)
        // =========================================================
        case MissionState::PRE_NAV_TO_HOME:
        {
           if (pre_move_step_ == 0) {
              // 1. Pose Estimate (위치 초기화) 수행
              RCLCPP_INFO(this->get_logger(), "Initializing Pose before Move (Home)...");
              publish_initial_pose();

              RCLCPP_INFO(this->get_logger(), "Step 2: Forward Push (Home)");
              pre_move_start_time_ = now;
              pre_move_step_ = 1;
           }
           else if(pre_move_step_ == 1) {
              if (now - pre_move_start_time_ >= std::chrono::milliseconds(500)) {
                  pre_move_step_ = 2;
                  pre_move_start_time_ = now;
              }
           }
           else if (pre_move_step_ == 2) {
               // [수정] 1.5초 동안 명령 지속 전송
               geometry_msgs::msg::Twist msg;
               msg.linear.x = 0.2; 
               cmd_vel_pre_pub_->publish(msg);

               if (now - pre_move_start_time_ >= std::chrono::milliseconds(2000)) {
                   geometry_msgs::msg::Twist stop_msg;
                   stop_msg.linear.x = 0.0;
                   cmd_vel_pre_pub_->publish(stop_msg);
                   
                   send_nav2_goal(home_pose_);
                   current_state_ = MissionState::NAV_TO_HOME;
                   
                   std_msgs::msg::String status; status.data = "RETURNING";
                   rpi_status_pub_->publish(status);
               }
           }
        }
        break;

        case MissionState::NAV_TO_HOME:
            if (nav2_goal_reached_ || start_flag) {
                start_flag = false;
                nav2_goal_reached_ = false;
                send_parking_goal();
                current_state_ = MissionState::PARKING_AT_HOME;
                std_msgs::msg::String status; status.data = "PARKING_AT_HOME";
                rpi_status_pub_->publish(status);
            }
        break;

        case MissionState::PARKING_AT_HOME: break;
    }
}

// [NEW] 주차 완료 위치 저장 함수 (TF 사용)
void MissionManager::save_parked_pose_from_tf() {
    try {
        // "map" 좌표계 기준 "base_link"의 위치를 조회
        geometry_msgs::msg::TransformStamped t;
        t = tf_buffer_->lookupTransform("map", "base_link", tf2::TimePointZero);

        last_parked_pose_.header.frame_id = "map";
        last_parked_pose_.header.stamp = this->now();
        last_parked_pose_.pose.position.x = t.transform.translation.x;
        last_parked_pose_.pose.position.y = t.transform.translation.y;
        last_parked_pose_.pose.position.z = 0.0;
        last_parked_pose_.pose.orientation = t.transform.rotation;

        RCLCPP_INFO(this->get_logger(), "Saved Parked Pose from TF: [%.2f, %.2f]", 
            last_parked_pose_.pose.position.x, last_parked_pose_.pose.position.y);

    } catch (const tf2::TransformException & ex) {
        RCLCPP_WARN(this->get_logger(), "Could not transform map to base_link: %s", ex.what());
    }
}

// [NEW] /initialpose 발행 함수
void MissionManager::publish_initial_pose() {
    geometry_msgs::msg::PoseWithCovarianceStamped init_msg;
    
    init_msg.header = last_parked_pose_.header;
    init_msg.header.stamp = this->now(); // 시간은 현재 시간으로 갱신
    init_msg.pose.pose = last_parked_pose_.pose;

    // 공분산(Covariance) 설정: 값이 작을수록 "이 위치가 확실하다"는 뜻
    for(int i=0; i<36; i++) init_msg.pose.covariance[i] = 0.0;
    
    init_msg.pose.covariance[0] = 0.1;  // X 분산 (작게)
    init_msg.pose.covariance[7] = 0.1;  // Y 분산 (작게)
    init_msg.pose.covariance[35] = 0.05; // Yaw 분산 (매우 작게)
    

    initial_pose_pub_->publish(init_msg);
    RCLCPP_INFO(this->get_logger(), "Published /initialpose to reset AMCL/Odom.");
}

// 주차 Action 요청
void MissionManager::send_parking_goal() {
  if (!parking_client_->wait_for_action_server(std::chrono::seconds(2))) {
    RCLCPP_ERROR(this->get_logger(), "Parking Action Server not available!");
    return;
  }

  auto goal_msg = ParkingAction::Goal();
  goal_msg.start_parking = true; 

  // 파라미터 값 설정
  if (current_state_ == MissionState::NAV_TO_TARGET) {
    goal_msg.stop_distance = 0.7;    
    goal_msg.slow_distance = 1.2;     
    goal_msg.forward_distance = 1.1;  
  } else if (current_state_ == MissionState::NAV_TO_HOME) {
    goal_msg.stop_distance = 0.603;   
    goal_msg.slow_distance = 1.1;      
    goal_msg.forward_distance = 1.0;   
  }

  RCLCPP_INFO(this->get_logger(), 
    "Sending Parking Goal -> Stop: %.2f", goal_msg.stop_distance);

  auto send_goal_options = rclcpp_action::Client<ParkingAction>::SendGoalOptions();
  send_goal_options.result_callback = 
      std::bind(&MissionManager::parking_result_callback, this, std::placeholders::_1);

  parking_client_->async_send_goal(goal_msg, send_goal_options);
}

// 주차 완료 콜백
void MissionManager::parking_result_callback(const GoalHandleParking::WrappedResult & result) {
  if (result.code == rclcpp_action::ResultCode::SUCCEEDED) {
    RCLCPP_INFO(this->get_logger(), "Parking Action Succeeded!");

    // [NEW] 주차 성공 시 현재 위치를 TF에서 읽어와 저장!
    save_parked_pose_from_tf();

    if (current_state_ == MissionState::PARKING_AT_TARGET) {
      current_state_ = MissionState::UNLOADING;
      unloading_step_ = 0;
    } 
    else if (current_state_ == MissionState::PARKING_AT_HOME) {
      RCLCPP_INFO(this->get_logger(), "Mission Complete! IDLE.");
      
      std_msgs::msg::String status; status.data = "IDLE";
      rpi_status_pub_->publish(status);
      
      current_state_ = MissionState::IDLE;
    }
  } 
  else if (result.code == rclcpp_action::ResultCode::ABORTED) {
    RCLCPP_ERROR(this->get_logger(), "Parking Action ABORTED (Marker lost or Timeout).");
    
    if (current_state_ == MissionState::PARKING_AT_TARGET) {
      current_state_ = MissionState::PRE_NAV_TO_TARGET;
      pre_move_step_ = 0;
    } 
    else if (current_state_ == MissionState::PARKING_AT_HOME) {
      current_state_ = MissionState::PRE_NAV_TO_HOME;
      pre_move_step_ = 0;
    }

  }
  else {
    RCLCPP_ERROR(this->get_logger(), "Parking Failed or Canceled.");
  }
}

// Nav2 Helper Functions
void MissionManager::send_nav2_goal(const geometry_msgs::msg::PoseStamped& pose) {
  if (!nav_client_->wait_for_action_server(std::chrono::seconds(2))) {
    RCLCPP_ERROR(this->get_logger(), "Nav2 Action Server not available!");
    return;
  }
  auto goal_msg = NavigateToPose::Goal();
  goal_msg.pose = pose;
  auto send_goal_options = rclcpp_action::Client<NavigateToPose>::SendGoalOptions();
  send_goal_options.result_callback = 
      std::bind(&MissionManager::nav2_result_callback, this, std::placeholders::_1);
      
  send_goal_options.feedback_callback = 
      std::bind(&MissionManager::nav2_feedback_callback, this, std::placeholders::_1, std::placeholders::_2);
  nav_client_->async_send_goal(goal_msg, send_goal_options);
}

void MissionManager::nav2_feedback_callback(
  GoalHandleNav::SharedPtr,
  const std::shared_ptr<const NavigateToPose::Feedback> feedback)
{
  // 남은 거리 (m)
  float distance_remaining = feedback->distance_remaining;
  
  // 남은 시간 (초)
  int eta_sec = feedback->estimated_time_remaining.sec;

  // 로그 출력 (필요시 rpi_status_pub_ 등으로 발행 가능)
  std_msgs::msg::Float64 rem_dist_msg;
  rem_dist_msg.data = distance_remaining;
  std_msgs::msg::Int32 rem_time_msg;
  rem_time_msg.data = eta_sec;
  remaindist_pub_->publish(rem_dist_msg);
  remaintime_pub_->publish(rem_time_msg);
}

void MissionManager::nav2_result_callback(const GoalHandleNav::WrappedResult & result) {
  if (result.code == rclcpp_action::ResultCode::SUCCEEDED) {
    RCLCPP_INFO(this->get_logger(), "Nav2 Goal Reached!");
    save_parked_pose_from_tf();
    nav2_goal_reached_ = true;
  }
  else if(result.code == rclcpp_action::ResultCode::ABORTED) {
    if (current_state_ == MissionState::NAV_TO_TARGET) {
      current_state_ = MissionState::PRE_NAV_TO_TARGET;
      pre_move_step_ = 0;
    } 
    else if (current_state_ == MissionState::NAV_TO_HOME) {
      current_state_ = MissionState::PRE_NAV_TO_HOME;
      pre_move_step_ = 0;
    }
  } 
  else {
    RCLCPP_ERROR(this->get_logger(), "Nav2 Failed or Canceled.");
  }
}

int main(int argc, char ** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MissionManager>());
  rclcpp::shutdown();
  return 0;
}
