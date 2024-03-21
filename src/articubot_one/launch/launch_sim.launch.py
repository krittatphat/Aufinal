import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription,RegisterEventHandler
from launch.event_handlers import (OnProcessStart,OnProcessExit)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
)
from launch_ros.actions import Node


def generate_launch_description():


    # Include the robot_state_publisher launch file, provided by our own package. Force sim time to be enabled
    # !!! MAKE SURE YOU SET THE PACKAGE NAME CORRECTLY !!!

    package_name='articubot_one' #<--- CHANGE ME

    rsp = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','rsp.launch.py'
                )]), launch_arguments={'use_sim_time': 'true'}.items()
    )

    # Include the Gazebo launch file, provided by the gazebo_ros package
    
    gazebo = ExecuteProcess(
        cmd=[
            "gazebo",
            "--verbose",
            "-s",
            "libgazebo_ros_factory.so",
            "-s",
            "libgazebo_ros_init.so",
            # "/home/white/final_ws/src/articubot_one/worlds/empty.world",
        ],
        output="screen",
    )

    # Run the spawner node from the gazebo_ros package. The entity name doesn't really matter if you only have a single robot.
    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', 'robot_description',
                                   '-entity', 'my_bot'],
                        output='screen')
    
    load_joint_state_controller = ExecuteProcess(
        cmd = ['ros2','control','load_controller','--set-state','start','joint_state_broadcaster'],
        output='screen'
    )

    load_arm_controller = ExecuteProcess(
        cmd = ['ros2','control','load_controller','--set-state','start','arm_controller'],
        output='screen'
    )

    node_controller = Node(
        package = "controller_manager",
        executable = "spawner",
        arguments = [
            "joint_state_broadcaster",
            "arm_controller",
        ],
    )



    # Launch them all!
    return LaunchDescription([
        RegisterEventHandler(
            event_handler = OnProcessExit(
                target_action=spawn_entity,
                on_exit = [load_joint_state_controller],
            )
        ),
        RegisterEventHandler(
            event_handler = OnProcessExit(
                target_action = load_joint_state_controller,
                on_exit = [load_arm_controller],
            )
        ),
        rsp,
        gazebo,
        spawn_entity,
        # node_controller,
    ])