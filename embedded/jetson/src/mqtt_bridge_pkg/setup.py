from setuptools import setup
import os
from glob import glob

package_name = 'mqtt_bridge_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # ▼▼▼ 여기부터 추가/수정하세요 ▼▼▼
        # 1. Launch 파일 설치
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        # 2. Config 파일 설치 (yaml)
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jetson',
    maintainer_email='jetson@todo.todo',
    description='MQTT Bridge for RPi Communication',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # 3. 실행 파일 연결
            'mqtt_bridge_node = mqtt_bridge_pkg.mqtt_bridge_node:main',
            'pose_publisher = mqtt_bridge_pkg.pose_publisher:main',
            'path_publisher = mqtt_bridge_pkg.path_publisher:main',
        ],
    },
)
