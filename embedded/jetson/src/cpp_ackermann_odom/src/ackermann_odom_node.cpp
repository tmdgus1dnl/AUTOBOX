#include <memory>
#include <chrono>
#include <cmath>
#include <thread>
#include <atomic>
#include <gpiod.hpp>

#include "rclcpp/rclcpp.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "std_msgs/msg/float64.hpp"
#include "geometry_msgs/msg/transform_stamped.hpp"
//#include "tf2_ros/transform_broadcaster.h"
#include "tf2/LinearMath/Quaternion.h"

using namespace std::chrono_literals;

class AckermannOdomNode : public rclcpp::Node {
public:
    AckermannOdomNode() : Node("ackermann_odom_node"), x_(0.0), y_(0.0), theta_(0.0) {
        // --- 파라미터 (로봇 사양에 맞춰 수정 필수) ---
        this->declare_parameter("wheelbase", 0.1375);       // 축간 거리 (m)
        this->declare_parameter("wheel_diameter", 0.065); // 바퀴 지름 (m)
        this->declare_parameter("ticks_per_rev", 720);
        this->declare_parameter("pin_a", 85);             // GPIO 12 (Pin 15)
        this->declare_parameter("pin_b", 144);              // GPIO 9 (Pin 7)

        // 1. GPIO 초기화 (libgpiod)
        int pin_a = this->get_parameter("pin_a").as_int();
        int pin_b = this->get_parameter("pin_b").as_int();
        
        chip_ = std::make_unique<gpiod::chip>("0");
        line_a_ = chip_->get_line(pin_a);
        line_b_ = chip_->get_line(pin_b);
        line_a_.request({"enc_a", gpiod::line_request::DIRECTION_INPUT, 0});
        line_b_.request({"enc_b", gpiod::line_request::DIRECTION_INPUT, 0});

        // 2. ROS 통신 설정
        // 오도메트리 발행
        odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>("odom_wheel", 10);
        //tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);
        
        // 조향각 구독 (Python 노드에서 발행해야 함)
        steering_sub_ = this->create_subscription<std_msgs::msg::Float64>(
            "steering_angle", 10, 
            std::bind(&AckermannOdomNode::steering_callback, this, std::placeholders::_1));

        last_time_ = this->now();

        // 3. 엔코더 폴링 스레드 시작
        running_ = true;
        encoder_thread_ = std::thread(&AckermannOdomNode::encoder_loop, this);

        // 4. 오도메트리 계산 타이머 (50Hz)
        timer_ = this->create_wall_timer(20ms, std::bind(&AckermannOdomNode::update_odometry, this));
        
        RCLCPP_INFO(this->get_logger(), "Ackermann Odometry Node Started!");
    }

    ~AckermannOdomNode() {
        running_ = false;
        if (encoder_thread_.joinable()) encoder_thread_.join();
    }

private:
    // 엔코더 펄스 카운팅 (별도 스레드)
    void encoder_loop() {
        int last_a = line_a_.get_value();
        while (running_) {
            int curr_a = line_a_.get_value();
            int curr_b = line_b_.get_value();

            if (curr_a != last_a) { 
                // A와 B가 다르면 정방향(증가), 같으면 역방향(감소)
                // (배선에 따라 반대일 수 있으니 테스트 후 부호 변경 필요)
                if (curr_a != curr_b) pulse_count_++;
                else pulse_count_--;
            }
            last_a = curr_a;
            std::this_thread::sleep_for(std::chrono::microseconds(10)); 
        }
    }

    // 조향각 데이터 수신 콜백
    void steering_callback(const std_msgs::msg::Float64::SharedPtr msg) {
        // 서보 모터 각도 (단위: radian, 왼쪽+, 오른쪽-)
        current_steering_angle_ = msg->data;
    }

    // 오도메트리 계산 및 발행
    void update_odometry() {
        auto current_time = this->now();
        double dt = (current_time - last_time_).seconds();

        // 이동 거리 계산
        long current_pulse = pulse_count_.load();
        long delta_pulse = current_pulse - last_pulse_count_;
        last_pulse_count_ = current_pulse;

        double ticks_per_rev = this->get_parameter("ticks_per_rev").as_double();
        double dia = this->get_parameter("wheel_diameter").as_double();
        double L = this->get_parameter("wheelbase").as_double();

        // 바퀴 이동 거리 (m)
        double delta_dist = (double(delta_pulse) / ticks_per_rev) * (dia * M_PI);

        // 선속도 (Linear Velocity)
        double v = delta_dist / dt;

        // 각속도 (Angular Velocity) - 애커만 조향 모델
        // w = (v / L) * tan(delta)
        double w = (v / L) * std::tan(current_steering_angle_);

        // 방향 변화량
        double delta_theta = w * dt; 

        // 좌표 업데이트 (Runge-Kutta 2nd order or Simple Euler)
        if (std::abs(w) > 0.001) {
            // 곡선 이동 시 더 정확한 계산
            x_ += (v / w) * (std::sin(theta_ + delta_theta) - std::sin(theta_));
            y_ -= (v / w) * (std::cos(theta_ + delta_theta) - std::cos(theta_));
        } else {
            // 직진 시
            x_ += delta_dist * std::cos(theta_);
            y_ += delta_dist * std::sin(theta_);
        }
        theta_ += delta_theta;

        // --- TF 발행 (odom -> base_link) ---
        /*
        geometry_msgs::msg::TransformStamped odom_tf;
        odom_tf.header.stamp = current_time;
        odom_tf.header.frame_id = "odom";
        odom_tf.child_frame_id = "base_link";
        odom_tf.transform.translation.x = x_;
        odom_tf.transform.translation.y = y_;
        odom_tf.transform.translation.z = 0.0; // 2D 이동이므로 0

        tf2::Quaternion q;
        q.setRPY(0, 0, theta_);
        odom_tf.transform.rotation.x = q.x();
        odom_tf.transform.rotation.y = q.y();
        odom_tf.transform.rotation.z = q.z();
        odom_tf.transform.rotation.w = q.w();
        tf_broadcaster_->sendTransform(odom_tf);
        */
        
        // ... (위치, 속도 계산 로직은 그대로 유지) ...

        // [수정] TF 변수(odom_tf)를 지웠으므로, odom 메시지에 직접 값을 넣어줍니다.
        nav_msgs::msg::Odometry odom;
        odom.header.stamp = current_time;
        odom.header.frame_id = "odom";       // 기준 좌표계 (보통 고정)
        odom.child_frame_id = "base_link";   // 로봇의 중심 좌표계
    
        // 위치 (Pose)
        odom.pose.pose.position.x = x_;
        odom.pose.pose.position.y = y_;
        odom.pose.pose.position.z = 0.0;
        
        // 쿼터니언 변환 (tf2::Quaternion은 헤더에 남겨두거나 여기서 사용)
        tf2::Quaternion q;
        q.setRPY(0, 0, theta_);
        odom.pose.pose.orientation.x = q.x();
        odom.pose.pose.orientation.y = q.y();
        odom.pose.pose.orientation.z = q.z();
        odom.pose.pose.orientation.w = q.w();
    
        // 공분산 설정 (EKF를 위해 필수)
        odom.pose.covariance[0] = 0.01;  // x 분산
        odom.pose.covariance[7] = 0.01;  // y 분산
        odom.pose.covariance[35] = 0.1;  // theta 분산 (엔코더 회전값은 오차가 크므로 약간 높게)
    
        // 속도 (Twist)
        odom.twist.twist.linear.x = v;
        odom.twist.twist.angular.z = w;
        odom.twist.covariance[0] = 0.01;
        odom.twist.covariance[35] = 0.1;
    
        // 변경된 토픽 이름("odom_wheel")으로 발행
        odom_pub_->publish(odom);
    
        last_time_ = current_time;
    }

    // 멤버 변수
    std::unique_ptr<gpiod::chip> chip_;
    gpiod::line line_a_, line_b_;
    
    std::atomic<long> pulse_count_{0}; 
    long last_pulse_count_ = 0;
    
    double x_, y_, theta_;
    double current_steering_angle_ = 0.0; // radian
    
    rclcpp::Time last_time_;
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr steering_sub_;
    //std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
    
    std::thread encoder_thread_;
    std::atomic<bool> running_;
};

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<AckermannOdomNode>());
    rclcpp::shutdown();
    return 0;
}
