import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'auron_robot_teleop'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Auron Robotics Engineer',
    maintainer_email='info@auronrobotics.com',
    description='Keyboard and joystick teleoperation package for Auron robot',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'teleop_keyboard = auron_robot_teleop.teleop_keyboard:main',
        ],
    },
)
