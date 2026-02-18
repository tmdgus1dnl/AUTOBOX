#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <cmath>

// Linux I2C 통신용 헤더
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"

using namespace std::chrono_literals;

class Mpu6050Node : public rclcpp::Node
{
public:
  Mpu6050Node()
  : Node("mpu6050_cpp_node"), bus_number_(7), device_address_(0x68)
  {
    // 1. I2C 버스 열기
    std::string i2c_bus = "/dev/i2c-" + std::to_string(bus_number_);
    i2c_file_ = open(i2c_bus.c_str(), O_RDWR);
    if (i2c_file_ < 0) {
      RCLCPP_ERROR(this->get_logger(), "I2C 버스를 열 수 없습니다. 권한을 확인하세요.");
      return;
    }

    if (ioctl(i2c_file_, I2C_SLAVE, device_address_) < 0) {
      RCLCPP_ERROR(this->get_logger(), "I2C 장치 주소를 설정할 수 없습니다.");
      return;
    }

    // 2. 센서 깨우기 (PWR_MGMT_1 레지스터 0x6B에 0 쓰기)
    i2c_smbus_write_byte_data(0x6B, 0x00);
    RCLCPP_INFO(this->get_logger(), "MPU6050 깨우기 완료. /imu/data_raw 발행 시작.");

    // 3. 퍼블리셔 및 타이머 설정 (20Hz = 50ms)
    publisher_ = this->create_publisher<sensor_msgs::msg::Imu>("/imu/data_raw", 10);
    timer_ = this->create_wall_timer(
      50ms, std::bind(&Mpu6050Node::timer_callback, this));
  }

  ~Mpu6050Node() {
    if (i2c_file_ >= 0) close(i2c_file_);
  }

private:
  int i2c_file_;
  int bus_number_;
  int device_address_;
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr publisher_;

  // I2C 쓰기 함수
  void i2c_smbus_write_byte_data(uint8_t reg, uint8_t value) {
    uint8_t buf[2] = {reg, value};
    write(i2c_file_, buf, 2);
  }

  // I2C 16비트 읽기 함수 (상위, 하위 바이트 결합)
  int16_t read_raw_data(uint8_t addr) {
    uint8_t reg[1] = {addr};
    write(i2c_file_, reg, 1);
    
    uint8_t buf[2];
    read(i2c_file_, buf, 2);
    
    int16_t value = (buf[0] << 8) | buf[1];
    return value;
  }

  void timer_callback()
  {
    auto msg = sensor_msgs::msg::Imu();

    msg.header.stamp = this->now();
    msg.header.frame_id = "imu_link";

    // 가속도 읽기 및 변환 (m/s^2)
    int16_t acc_x = read_raw_data(0x3B);
    int16_t acc_y = read_raw_data(0x3D);
    int16_t acc_z = read_raw_data(0x3F);

    msg.linear_acceleration.x = (acc_x / 16384.0) * 9.80665;
    msg.linear_acceleration.y = (acc_y / 16384.0) * 9.80665;
    msg.linear_acceleration.z = (acc_z / 16384.0) * 9.80665;

    // 각속도 읽기 및 변환 (rad/s)
    int16_t gyro_x = read_raw_data(0x43);
    int16_t gyro_y = read_raw_data(0x45);
    int16_t gyro_z = read_raw_data(0x47);

    msg.angular_velocity.x = (gyro_x / 131.0) * (M_PI / 180.0);
    msg.angular_velocity.y = (gyro_y / 131.0) * (M_PI / 180.0);
    msg.angular_velocity.z = (gyro_z / 131.0) * (M_PI / 180.0);

    // 공분산 설정 (EKF 및 필터용)
    msg.linear_acceleration_covariance[0] = 0.04;
    msg.linear_acceleration_covariance[4] = 0.04;
    msg.linear_acceleration_covariance[8] = 0.04;

    msg.angular_velocity_covariance[0] = 0.02;
    msg.angular_velocity_covariance[4] = 0.02;
    msg.angular_velocity_covariance[8] = 0.02;

    // 필터에 방향 데이터가 없음을 알림
    msg.orientation_covariance[0] = -1.0;

    publisher_->publish(msg);
  }
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Mpu6050Node>());
  rclcpp::shutdown();
  return 0;
}
