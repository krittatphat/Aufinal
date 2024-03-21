#!/usr/bin/env python3
# Copyright 2011 Brown University Robotics.
# Copyright 2017 Open Source Robotics Foundation, Inc.
# All rights reserved.
#
# Software License Agreement (BSD License 2.0)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of the Willow Garage nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import sys
import math
import geometry_msgs.msg
import rclpy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import subprocess

if sys.platform == "win32":
    import msvcrt
else:
    import termios
    import tty


msg = """
This node takes keypresses from the keyboard and publishes them
as Twist messages. It works best with a US keyboard layout.
---------------------------
Moving around:
   q    w    e
   a    x    d
   z    s    c

anything else : stop

</> : increase/decrease max speeds by 10%
-/= : increase/decrease only linear speed by 10%
[/] : increase/decrease only angular speed by 10%

t/y: increase/decrease joint 1 angle (degree)
g/h: increase/decrease joint 2 angle (degree)
b/n: increase/decrease joint 3 angle (degree)
u/i: increase/decrease joint 4 angle (degree)
j/k: increase/decrease joint 5 angle (degree)
o/p: enable/disable gripper

Press R to apply arm position.
Press 0 to set zero position.

CTRL-C to quit
"""

moveBindings = {
    "w": (1, 0, 0, 0),
    "e": (1, 0, 0, -1),
    "a": (0, 0, 0, 1),
    "d": (0, 0, 0, -1),
    "q": (1, 0, 0, 1),
    "s": (-1, 0, 0, 0),
    "c": (-1, 0, 0, 1),
    "z": (-1, 0, 0, -1),
    "E": (1, -1, 0, 0),
    "W": (1, 0, 0, 0),
    "A": (0, 1, 0, 0),
    "D": (0, -1, 0, 0),
    "Q": (1, 1, 0, 0),
    "S": (-1, 0, 0, 0),
    "C": (-1, -1, 0, 0),
    "Z": (-1, 1, 0, 0),
    "1": (0, 0, 1, 0),
    "2": (0, 0, -1, 0),
}

speedBindings = {
    ".": (1.1, 1.1),
    ",": (0.9, 0.9),
    "=": (1.1, 1),
    "-": (0.9, 1),
    "]": (1, 1.1),
    "[": (1, 0.9),
}

arm = {
    "t":(0.0),
    "y":(0.0),
    "g":(0.0),
    "h":(0.0),
    "r":(0.0),
}



def getKey(settings):
    if sys.platform == "win32":
        # getwch() returns a string on Windows
        key = msvcrt.getwch()
    else:
        tty.setraw(sys.stdin.fileno())
        # sys.stdin.read() returns a string on Linux
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def saveTerminalSettings():
    if sys.platform == "win32":
        return None
    return termios.tcgetattr(sys.stdin)


def restoreTerminalSettings(old_settings):
    if sys.platform == "win32":
        return
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def vels(speed, turn):
    return "currently:\tspeed %s\tturn %s " % (speed, turn)

def deg2rad(deg):
    rad = deg * (math.pi /180)
    return rad

def rad2deg(rad):
    deg = rad * (180 / math.pi)
    return deg

def main():
    settings = saveTerminalSettings()

    rclpy.init()

    node = rclpy.create_node("teleop_twist_keyboard")
    pub = node.create_publisher(geometry_msgs.msg.Twist, "cmd_vel", 10)

    speed = 0.5
    turn = 1.0
    x = 0.0
    y = 0.0
    z = 0.0
    th = 0.0
    status = 0.0

    position_1 = 0.0
    position_2 = 0.0

    

    move_command_template = '''ros2 topic pub -1 /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \
    '{{
        header: {{
            stamp: {{sec: {}, nanosec: {}}},
            frame_id: "base_link"
        }},
        joint_names: ["sup_grip_joint", "gripper_joint"],
        points: [{{
            positions: [{}],
            time_from_start: {{sec: {}, nanosec: {}}}
        }}]
    }}\''''

    sec_value = 0
    nanosec_value = 0
    time_sec = 3
    time_nanosec = 0

    try:
        print(msg)
        print(vels(speed, turn))
        while True:
            positions_format = '{:.1f}, {:.1f}'.format(position_1, position_2)
            move_command = move_command_template.format(sec_value, nanosec_value, positions_format, time_sec, time_nanosec)
            key = getKey(settings)
            if key in moveBindings.keys():
                x = moveBindings[key][0]
                y = moveBindings[key][1]
                z = moveBindings[key][2]
                th = moveBindings[key][3]
            elif key in arm.keys():
                if key == 't':
                    position_1 = 0.0
                    print("slide down")
                if key == 'y':
                    position_1 = -0.17
                    print("slide up")
                if key == 'g':
                    position_2 = 0.0
                    print("grip up")
                if key == 'h':
                    position_2 = 3.14
                    print("grip down")
                if key == 'r':
                    subprocess.run(move_command,shell=True)

            elif key in speedBindings.keys():
                speed = speed * speedBindings[key][0]
                turn = turn * speedBindings[key][1]

                print(vels(speed, turn))
                if status == 14:
                    print(msg)
                status = (status + 1) % 15
            else:
                x = 0.0
                y = 0.0
                z = 0.0
                th = 0.0
                
                if key == "\x03":
                    break
            
            twist = geometry_msgs.msg.Twist()
            twist.linear.x = x * speed
            twist.linear.y = y * speed
            twist.linear.z = z * speed
            twist.angular.x = 0.0
            twist.angular.y = 0.0
            twist.angular.z = th * turn
            pub.publish(twist)

            
            
            



            

    except Exception as e:
        print(e)

    finally:
        twist = geometry_msgs.msg.Twist()
        twist.linear.x = 0.0
        twist.linear.y = 0.0
        twist.linear.z = 0.0
        twist.angular.x = 0.0
        twist.angular.y = 0.0
        twist.angular.z = 0.0
        pub.publish(twist)
        restoreTerminalSettings(settings)


if __name__ == "__main__":
    main()