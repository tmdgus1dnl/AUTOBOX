#!/usr/bin/env python3
import rclpy
import math
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64

# --- HW imports (DC motor HAT / Servo) ---
import busio
import board
from adafruit_pca9685 import PCA9685
from adafruit_servokit import ServoKit 

class PWMThrottleHat:
    def __init__(self, pwm):
        self.pwm = pwm
        self.pwm.frequency = 60  # 주파수 설정

    def set_throttle(self, channel, throttle):
        pulse = int(0xFFFF * abs(throttle))  # 16비트 듀티 사이클 계산
        if channel == 0:  # MA1, MA2 포트용
            self.pwm_pin = 5
            self.in1_pin = 4
            self.in2_pin = 3
        else:               # MB1, MB2 포트용
            self.pwm_pin = 0
            self.in1_pin = 1
            self.in2_pin = 2
        if throttle < 0:      # 전진
            self.pwm.channels[self.pwm_pin].duty_cycle = pulse
            self.pwm.channels[self.in1_pin].duty_cycle = 0
            self.pwm.channels[self.in2_pin].duty_cycle = 0xFFFF
        elif throttle > 0:    # 후진
            self.pwm.channels[self.pwm_pin].duty_cycle = pulse
            self.pwm.channels[self.in1_pin].duty_cycle = 0xFFFF
            self.pwm.channels[self.in2_pin].duty_cycle = 0
        else:                 # 정지
            self.pwm.channels[self.pwm_pin].duty_cycle = 0
            self.pwm.channels[self.in1_pin].duty_cycle = 0
            self.pwm.channels[self.in2_pin].duty_cycle = 0


class RCCarNode(Node):

    def __init__(self):
        super().__init__('rc_car_node')

        # ---- Parameters ----
        self.declare_parameter('cmd_vel_act', '/cmd_vel_act')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel_final')
        self.declare_parameter('control_rate', 20.0)   # Hz
        self.declare_parameter('cmd_timeout', 0.2)     # sec

        # 디버그용: 실제로 적용한 cmd를 재발행할지
        self.declare_parameter('publish_applied_cmd', True)
        self.declare_parameter('applied_cmd_topic', '/rc_car/applied_cmd_vel')

        # ---- HW Parameters ----

        self.declare_parameter('motor_channel', 0)        # PWMThrottleHat(channel=0) :contentReference[oaicite:5]{index=5}


        self.declare_parameter('servo_pca_address', 0x60)
        self.declare_parameter('servo_channel', 0)        # kit.servo[0] :contentReference[oaicite:7]{index=7}
        self.declare_parameter('steer_center_deg', 100.0) # pan=100 :contentReference[oaicite:8]{index=8}
        self.declare_parameter('wheelbase_m',0.1375)
        
        self.cmd_vel_act = self.get_parameter('cmd_vel_act').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.control_rate = float(self.get_parameter('control_rate').value)
        self.cmd_timeout = float(self.get_parameter('cmd_timeout').value)

        self.publish_applied_cmd = bool(self.get_parameter('publish_applied_cmd').value)
        self.applied_cmd_topic = self.get_parameter('applied_cmd_topic').value

        self.motor_channel = int(self.get_parameter('motor_channel').value)

        self.servo_pca_address = int(self.get_parameter('servo_pca_address').value)
        self.servo_channel = int(self.get_parameter('servo_channel').value)
        self.steer_center_deg = float(self.get_parameter('steer_center_deg').value)
        self.wheelbase_m = float(self.get_parameter('wheelbase_m').value)
        self.steering_pub = self.create_publisher(Float64, 'steering_angle', 10)

        # ---- State ----
        self._v_cmd = 0.0
        self._w_cmd = 0.0
        self._last_cmd_time = self.get_clock().now()

        # ---- ROS I/O ----
        self._sub_cmd = self.create_subscription(
            Twist, self.cmd_vel_topic, self._on_cmd_vel, 10
        )
        self._sub_act = self.create_subscription(
            Float64, self.cmd_vel_act, self._on_act_vel, 10
        )
        
        self._pub_applied = None
        if self.publish_applied_cmd:
            self._pub_applied = self.create_publisher(Twist, self.applied_cmd_topic, 10)

        period = 1.0 / self.control_rate if self.control_rate > 0 else 0.02
        self._timer = self.create_timer(period, self._control_loop)

        self.get_logger().info(
            f'rc_car_node: sub={self.cmd_vel_topic}, rate={self.control_rate}Hz, '
            f'timeout={self.cmd_timeout}s'
        )

        # ---- Hardware init ----
        self._init_hardware()

    # -----------------------------
    # Hardware init/deinit
    # -----------------------------
    def _init_hardware(self):
 
        self._i2c = busio.I2C(board.SCL, board.SDA)


        self._motor_pca = PCA9685(self._i2c)
        self._motor_pca.frequency = 60
        self.motor_hat = PWMThrottleHat(self._motor_pca)


        self.servo_kit = ServoKit(channels=16, i2c=self._i2c, address=self.servo_pca_address)

        self.servo_kit.servo[self.servo_channel].angle = self.steer_center_deg

        self.get_logger().info(
            f'HW init OK: ch={self.motor_channel}, '
            f'servo_pca=0x{self.servo_pca_address:02x} ch={self.servo_channel} center={self.steer_center_deg}'
        )

    def _deinit_hardware(self):

        try:
            self.motor_hat.set_throttle(0, 0.0)
        except Exception:
            pass
        try:
            self.servo_kit.servo[self.servo_channel].angle = self.steer_center_deg
        except Exception:
            pass
        try:
            self._motor_pca.deinit()
        except Exception:
            pass

    # -----------------------------
    # ROS callbacks / loops
    # -----------------------------
    def _on_cmd_vel(self, msg: Twist):
        self._v_cmd = float(msg.linear.x)
        self._w_cmd = float(msg.angular.z)
        self._last_cmd_time = self.get_clock().now()
    
    def _on_act_vel(self, msg: Float64):
        self.motor_hat.set_throttle(1, msg.data)

    def _control_loop(self):

        age = (self.get_clock().now() - self._last_cmd_time).nanoseconds * 1e-9
        if age > self.cmd_timeout:
            v, w = 0.0, 0.0
        else:
            v, w = self._v_cmd, self._w_cmd


        try:
            self.apply_control(v, w)
        except Exception as e:
            self.get_logger().error(f'apply_control error: {e}')
  
            try:
                self.apply_control(0.0, 0.0)
            except Exception:
                pass


        if self._pub_applied is not None:
            out = Twist()
            out.linear.x = float(v)
            out.angular.z = float(w)
            self._pub_applied.publish(out)

    # -----------------------------
    @staticmethod
    def speed_to_pwm(target_speed_mps):
        if abs(target_speed_mps) < 0.01:
            return 0.0

        pwm = (1.1734 * abs(target_speed_mps)) + 0.1385

        MIN_PWM = 0.15 
        MAX_PWM = 1.0

        pwm = max(MIN_PWM, min(MAX_PWM, pwm))
    
        if target_speed_mps < 0:
            return -pwm
        else:
            return pwm
    # -----------------------------
    def apply_control(self, v: float, w: float):
        if abs(v) < 0.02:
            throttle = 0.0
            steer_delta = 0.0
            servo_deg = self.steer_center_deg
        else:
            throttle = self.speed_to_pwm(v)
            # 선속도가 너무 작아 0으로 나누어지는 것 방지
            if abs(v) < 0.01:
                steer_delta = 0.0 
            else:
                steer_delta = -math.atan(self.wheelbase_m * w / v)
            steer_deg = steer_delta*(180/math.pi)
            servo_deg = (0.0012*steer_deg*steer_deg*steer_deg) - (0.0267*steer_deg*steer_deg) + 2.378*steer_deg + 100
            servo_deg = max(50, min(140,servo_deg))
        # --- output apply 
        self.motor_hat.set_throttle(0, throttle)                 # :contentReference[oaicite:10]{index=10}
        self.servo_kit.servo[self.servo_channel].angle = servo_deg  # :contentReference[oaicite:11]{index=11}

        msg = Float64()
        msg.data = steer_delta
        self.steering_pub.publish(msg)

    def destroy_node(self):

        try:
            self.apply_control(0.0, 0.0)
        except Exception:
            pass
        self._deinit_hardware()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RCCarNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
