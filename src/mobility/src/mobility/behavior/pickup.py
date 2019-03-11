#! /usr/bin/env python

from __future__ import print_function

import sys
import rospy 
import math
import random 
import tf
import angles 

from std_msgs.msg import String
from geometry_msgs.msg import Point 

from mobility.msg import MoveResult
from swarmie_msgs.msg import Obstacle

from mobility.swarmie import swarmie, TagException, HomeException, ObstacleException, PathException, AbortException

'''Pickup node.'''


def setup_first_approach():
    """Drive a little closer to the nearest block if it's far enough away."""
    global claw_offset_distance
    extra_offset = 0.20

    swarmie.fingers_open()
    swarmie.set_wrist_angle(1.15)
    rospy.sleep(1)

    block = swarmie.get_nearest_block_location(targets_buffer_age=5.0)

    if block is not None:
        print("Getting setup for pickup.")
        cur_loc = swarmie.get_odom_location().get_pose()
        dist = math.hypot(cur_loc.x - block.x, cur_loc.y - block.y)

        if dist > (claw_offset_distance + extra_offset):
            swarmie.drive_to(
                block,
                claw_offset=claw_offset_distance+extra_offset,
                ignore=Obstacle.VISION_SAFE | Obstacle.IS_SONAR
            )


def approach(setup_claw=True):
    global claw_offset_distance
    print ("Attempting a pickup.")

    if setup_claw:
        swarmie.fingers_open()
        swarmie.set_wrist_angle(1.15)
        rospy.sleep(1)
    else:
        rospy.sleep(0.25)

    block = swarmie.get_nearest_block_location(targets_buffer_age=0.5)

    if block is not None:
        # claw_offset should be a positive distance of how short drive_to needs to be.
        swarmie.drive_to(
            block,
            claw_offset=claw_offset_distance,
            ignore=Obstacle.VISION_SAFE | Obstacle.IS_SONAR
        )
        # Grab - minimal pickup with sim_check.

        if swarmie.simulator_running():
            finger_close_angle = 0
        else:
            finger_close_angle = 0.5

        swarmie.set_finger_angle(finger_close_angle) #close
        rospy.sleep(1)
        swarmie.wrist_up()
        rospy.sleep(.5)
        # did we succesuflly grab a block?
        if swarmie.has_block():
            swarmie.wrist_middle()
            swarmie.drive(-0.3,
                          ignore=Obstacle.VISION_SAFE | Obstacle.IS_SONAR)
            return True
        else:
            swarmie.set_wrist_angle(0.55)
            rospy.sleep(1)
            swarmie.fingers_open()
            # Wait a moment for a block to fall out of claw
            rospy.sleep(0.25)
    else:
        print("No legal blocks detected.")
        swarmie.wrist_up()
        sys.exit(1)

    # otherwise reset claw and return Falase
    swarmie.wrist_up()
    return False

def recover():
    global claw_offset_distance

    if not swarmie.simulator_running():
        claw_offset_distance -= 0.02
    else:
        claw_offset_distance += 0.02

    print ("Missed, trying to recover.")
    try:
        swarmie.drive(-0.15,
                      ignore=Obstacle.VISION_SAFE | Obstacle.IS_SONAR)
        # Wait a moment to detect tags before possible backing up further
        rospy.sleep(0.25)

        block = swarmie.get_nearest_block_location(targets_buffer_age=1.0)

        if block is not None:
            pass
        else:
            swarmie.drive(-0.15,
                          ignore=Obstacle.VISION_SAFE | Obstacle.IS_SONAR)

        #swarmie.turn(math.pi/2)
        #swarmie.turn(-math.pi)
        #swarmie.turn(math.pi/2)
    except: 
        print("Oh no, we have an exception!")

def main(**kwargs):
    global claw_offset_distance
    
    claw_offset_distance = 0.24 
    if swarmie.simulator_running():
        claw_offset_distance = 0.17

    setup_first_approach()

    for i in range(3):
        if approach(setup_claw=bool(i > 0)):
            print ("Got it!")
            sys.exit(0)        
        recover()
        
    print ("Giving up after too many attempts.")
    return 1

if __name__ == '__main__' : 
    swarmie.start(node_name='pickup')
    sys.exit(main())
