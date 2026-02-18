#include <rclcpp/rclcpp.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>

#include <tf2_ros/transform_broadcaster.h>
#include <tf2/LinearMath/Quaternion.h>

#include <chrono>
#include <cmath>
#include <memory>
#include <string>

class FakeOdomNode : public rclcpp::Node {
public:
  FakeOdomNode() : Node("fake_odom_node")
  {
    // ---- Parameters (원하면 launch에서 바꿀 수 있게) ----
    this->declare_parameter<std::string>("cmd_vel_topic", "/cmd_vel");
    this->declare_parameter<std::string>("odom_topic", "/odom");
    this->declare_parameter<std::string>("odom_frame", "odom");
    this->declare_parameter<std::string>("base_frame", "base_link");
    this->declare_parameter<double>("publish_rate_hz", 20.0);

    cmd_vel_topic_ = this->get_parameter("cmd_vel_topic").as_string();
    odom_topic_    = this->get_parameter("odom_topic").as_string();
    odom_frame_    = this->get_parameter("odom_frame").as_string();
    base_frame_    = this->get_parameter("base_frame").as_string();
    publish_rate_hz_ = this->get_parameter("publish_rate_hz").as_double();

    if (publish_rate_hz_ <= 0.0) publish_rate_hz_ = 20.0;

    // ---- Pub/Sub ----
    odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>(odom_topic_, 10);

    cmd_sub_ = this->create_subscription<geometry_msgs::msg::Twist>(
      cmd_vel_topic_, 10,
      std::bind(&FakeOdomNode::onCmdVel, this, std::placeholders::_1)
    );

    tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(this);

    // ---- State ----
    x_ = 0.0;
    y_ = 0.0;
    yaw_ = 0.0;
    v_ = 0.0;
    w_ = 0.0;

    last_time_ = this->get_clock()->now();

    // ---- Timer ----
    using namespace std::chrono_literals;
    auto period_ms = static_cast<int>(1000.0 / publish_rate_hz_);
    if (period_ms < 1) period_ms = 1;

    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(period_ms),
      std::bind(&FakeOdomNode::onTimer, this)
    );

    RCLCPP_INFO(this->get_logger(),
                "FakeOdomNode started. cmd_vel=%s, odom=%s, frames: %s -> %s, rate=%.1fHz",
                cmd_vel_topic_.c_str(), odom_topic_.c_str(),
                odom_frame_.c_str(), base_frame_.c_str(), publish_rate_hz_);
  }

private:
  void onCmdVel(const geometry_msgs::msg::Twist::SharedPtr msg)
  {
    // Nav2가 내는 cmd_vel을 저장해두고 timer에서 적분
    v_ = msg->linear.x;     // m/s
    w_ = msg->angular.z;    // rad/s
  }

  void onTimer()
  {
    auto now = this->get_clock()->now();

    // dt 계산 (초)
    double dt = (now - last_time_).seconds();
    last_time_ = now;

    // 혹시 dt가 비정상적으로 큰 경우(디버깅 중 일시정지 등) 안정화
    if (dt <= 0.0) dt = 0.0;
    if (dt > 0.2)  dt = 0.2;  // 200ms 이상은 잘라버림 (테스트용 안전장치)

    // ---- 적분 ----
    // 전진 속도 v_를 현재 yaw_ 방향으로 적분
    x_ += v_ * std::cos(yaw_) * dt;
    y_ += v_ * std::sin(yaw_) * dt;
    yaw_ += w_ * dt;

    // yaw를 [-pi, pi]로 정규화
    yaw_ = std::atan2(std::sin(yaw_), std::cos(yaw_));

    // ---- Quaternion (yaw만) ----
    tf2::Quaternion q;
    q.setRPY(0.0, 0.0, yaw_);
    q.normalize();

    // ---- odom message ----
    nav_msgs::msg::Odometry odom;
    odom.header.stamp = now;
    odom.header.frame_id = odom_frame_;
    odom.child_frame_id = base_frame_;

    odom.pose.pose.position.x = x_;
    odom.pose.pose.position.y = y_;
    odom.pose.pose.position.z = 0.0;

    odom.pose.pose.orientation.x = q.x();
    odom.pose.pose.orientation.y = q.y();
    odom.pose.pose.orientation.z = q.z();
    odom.pose.pose.orientation.w = q.w();

    // twist도 채워주면 velocity_smoother 등에서 참고 가능
    odom.twist.twist.linear.x  = v_;
    odom.twist.twist.linear.y  = 0.0;
    odom.twist.twist.angular.z = w_;

    odom_pub_->publish(odom);

    // ---- TF: odom -> base_link ----
    geometry_msgs::msg::TransformStamped tf;
    tf.header.stamp = now;
    tf.header.frame_id = odom_frame_;
    tf.child_frame_id = base_frame_;

    tf.transform.translation.x = x_;
    tf.transform.translation.y = y_;
    tf.transform.translation.z = 0.0;

    tf.transform.rotation.x = q.x();
    tf.transform.rotation.y = q.y();
    tf.transform.rotation.z = q.z();
    tf.transform.rotation.w = q.w();

    tf_broadcaster_->sendTransform(tf);
  }

private:
  // Pub/Sub
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_sub_;
  std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
  rclcpp::TimerBase::SharedPtr timer_;

  // Params
  std::string cmd_vel_topic_;
  std::string odom_topic_;
  std::string odom_frame_;
  std::string base_frame_;
  double publish_rate_hz_;

  // State
  double x_, y_, yaw_;
  double v_, w_;
  rclcpp::Time last_time_;
};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<FakeOdomNode>());
  rclcpp::shutdown();
  return 0;
}
