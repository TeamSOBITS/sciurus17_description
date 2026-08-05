# Copyright 2023 RT Corporation

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from sciurus17_description.robot_description_loader import RobotDescriptionLoader


def generate_launch_description():
    description_loader = RobotDescriptionLoader()
    declare_kachaka_arg = DeclareLaunchArgument(
        'use_kachaka_base', default_value='false', description='Enable Kachaka mobile base')
    use_kachaka = LaunchConfiguration('use_kachaka_base')
    description_loader.use_kachaka_base = use_kachaka

    component_args = ['enable_head', 'enable_arm_right', 'enable_arm_left',
                      'enable_gripper_right', 'enable_gripper_left']

    declare_components = [
        DeclareLaunchArgument(name, default_value='true', description='Build this component.')
        for name in component_args
    ]
    for name in component_args:
        setattr(description_loader, name, LaunchConfiguration(name))

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[{'robot_description': ParameterValue(description_loader.load(), value_type=str)}],
    )
    jsp = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        output='screen',
    )

    rviz_config_file = (
        get_package_share_directory('sciurus17_description') + '/launch/display.rviz'
    )
    rviz = Node(
        name='rviz2',
        package='rviz2',
        executable='rviz2',
        output='log',
        arguments=['-d', rviz_config_file],
    )

    return LaunchDescription(
        [
            declare_kachaka_arg,
            *declare_components,
            rsp,
            jsp,
            rviz,
        ]
    )
