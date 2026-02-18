"""

Path tracking simulation with Stanley steering control and PID speed control.

author: Atsushi Sakai (@Atsushi_twi)

Reference:
    - [Stanley: The robot that won the DARPA grand challenge](http://isl.ecst.csuchico.edu/DOCS/darpa2005/DARPA%202005%20Stanley.pdf)
    - [Autonomous Automobile Path Tracking](https://www.ri.cmu.edu/pub_files/2009/2/Automatic_Steering_Methods_for_Autonomous_Automobile_Path_Tracking.pdf)

"""
import numpy as np
import matplotlib.pyplot as plt
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))
#from utils.angle import angle_mod
#from PathPlanning.CubicSpline import cubic_spline_planner

k = 0.3   # Control gain (반응 민감도, 필요시 튜닝: 2.0 ~ 6.0)
Kp = 1.0       # Speed proportional gain
dt = 0.1  # [s] time difference
L = 0.1375     # [m] Wheel base (13.75cm)
max_steer = np.radians(20.0)  # [rad] max steering angle (20도)

show_animation = True


class State:
    """
    Class representing the state of a vehicle.

    :param x: (float) x-coordinate
    :param y: (float) y-coordinate
    :param yaw: (float) yaw angle
    :param v: (float) speed
    """

    def __init__(self, x=0.0, y=0.0, yaw=0.0, v=0.0):
        self.x = x
        self.y = y
        self.yaw = yaw
        self.v = v

    def update(self, a, delta):
        # Simulation only
        self.x += self.v * np.cos(self.yaw) * 0.1
        self.y += self.v * np.sin(self.yaw) * 0.1
        self.yaw += self.v / L * np.tan(delta) * 0.1
        self.v += a * 0.1


def pid_control(target, current):
    """
    Proportional control for the speed.

    :param target: (float)
    :param current: (float)
    :return: (float)
    """
    return Kp * (target - current)


def stanley_control(state, cx, cy, cyaw, last_target_idx, gear=1, last_yaw = 0):
    """
    Stanley steering control for Forward and Backward driving.
    
    :param gear: 1 for Forward, -1 for Backward
    """
    current_target_idx, error_front_axle = calc_target_index(state, cx, cy)

    if last_target_idx >= current_target_idx:
        current_target_idx = last_target_idx

    # 1. Heading Error Calculation
    # 후진 시에는 차량의 진행 방향(Rear)과 경로의 방향을 맞춰야 합니다.
    # 전진: Path - Car
    # 후진: (Path - Car) 의 반대 or Car - Path?
    # 분석 결과: 후진 시 '헤딩 오차'의 부호를 반대로 적용해야 안정적입니다.
    theta_e = normalize_angle(cyaw[current_target_idx] - state.yaw)

    
    # 2. Cross Track Error (CTE) Calculation
    # arctan term: 속도가 0일 때 분모 0 방지
    v_safe = state.v if abs(state.v) > 0.01 else 0.01 * gear
    
    # 후진 시에는 속도 부호(v)가 음수이므로 arctan 항의 부호가 자동으로 바뀌어
    # 조향 반전 효과가 나타납니다. 하지만 '진행 방향 기준'으로 생각하기 위해
    # 절대값 속도를 사용하고 gear에 따라 로직을 분기하는 것이 명확할 때가 많습니다.
    # 여기서는 Stanley 원본 수식을 따르되 v의 부호를 그대로 이용합니다.
    # (v가 음수면 조향이 반대로 들어감 -> 후진 시 기구학과 일치)
    #theta_d = np.arctan2(k * error_front_axle, v_safe)
    theta_d = np.arctan((k*error_front_axle) / v_safe)
    
    print(f"\ntheta_e : {theta_e:.2f}, theta_d : {theta_d:.2f}")
    print(f" error_x : {error_front_axle:.2f}")
    # 3. Final Steering Angle
    
    delta = theta_e + theta_d
    
    if gear == 1:
      if last_yaw > 0 and delta < 0:
        delta = 0
      elif last_yaw < 0 and delta > 0:
        delta = 0

    
    # 후진 주행 특성상 조향각 제한을 엄격히 하는 것이 좋습니다.
    delta = np.clip(delta, -max_steer, max_steer)

    return delta, current_target_idx


def normalize_angle(angle):
    """
    Normalize an angle to [-pi, pi].
    """
    while angle > np.pi:
        angle -= 2.0 * np.pi
    while angle < -np.pi:
        angle += 2.0 * np.pi
    return angle

'''
def calc_target_index(state, cx, cy):
    """
    Compute index in the trajectory list of the target.
    """
    # Calc front axle position
    # 주의: 후진 Stanley에서도 '조향축(Front Axle)' 기준으로 오차를 계산하는 것이
    # 수식적으로 일반적입니다 (Reversing car trajectory tracking papers 참고).
    fx = state.x + L * np.cos(state.yaw)
    fy = state.y + L * np.sin(state.yaw)

    # Search nearest point index
    dx = [fx - icx for icx in cx]
    dy = [fy - icy for icy in cy]
    d = np.hypot(dx, dy)
    target_idx = np.argmin(d)

    # Project RMS error onto front axle vector
    front_axle_vec = [-np.cos(state.yaw + np.pi / 2),
                      -np.sin(state.yaw + np.pi / 2)]
    error_front_axle = np.dot([dx[target_idx], dy[target_idx]], front_axle_vec)

    return target_idx, error_front_axle
'''

def calc_target_index(state, cx, cy):
    """
    Compute index in the trajectory list of the target.
    """
    # Calc front axle position
    fx = state.x - L * np.sin(state.yaw)
    fy = state.y + L * np.cos(state.yaw)

    # Search nearest point index
    dx = [fx - icx for icx in cx]
    dy = [fy - icy for icy in cy]
    d = np.hypot(dx, dy)
    target_idx = np.argmin(d)

    # [핵심 수정] 오차 투영 벡터 회전 (90도 보정 제거)
    # 기존: [-np.cos(state.yaw + np.pi / 2), -np.sin(...)] -> Y축 오차만 계산됨
    # 수정: [-np.cos(state.yaw), -np.sin(state.yaw)] -> X축(좌우) 오차를 계산함
    
    front_axle_vec = [-np.cos(state.yaw), -np.sin(state.yaw)]
    
    error_front_axle = np.dot([dx[target_idx], dy[target_idx]], front_axle_vec)

    return target_idx, error_front_axle
