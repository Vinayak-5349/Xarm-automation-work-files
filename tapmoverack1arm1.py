import time
from xarm.wrapper import XArmAPI

xarm_ip = "192.168.1.159"
arm = XArmAPI(xarm_ip)
arm.connect()
arm.clean_error()
arm.clean_warn()
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(0)
def move_along_tool_x(dx, speed=20):
    #timed_call("tool_move", {"dx": dx, "dy": 0, "dz": 0, "speed": speed},
               arm.set_tool_position( dx, 0, 0, 0, 0, 0, speed=speed, wait=True)
def timed_sleep(duration):
    time.sleep(duration)
    #record_step("sleep", {"duration": duration}, duration)
def move_to_cartesian(cartesian_position, speed=20):
    status_code, joint_angles = arm.get_inverse_kinematics(cartesian_position, input_is_radian=False, return_is_radian=False)
    if status_code != 0 or not joint_angles:
        print("Failed to calculate inverse kinematics.")
        return
    joint_angles = [float(angle) for angle in joint_angles[:6]]
    arm.set_servo_angle(angle=joint_angles, speed=speed, is_radian=False, wait=True)


move_to_cartesian([59,608.9,-6.4,6.7,1,173.1],speed=75)  
# timed_sleep(1.5)
# fist common point (for both swipe,tap and insert )


# move_to_cartesian([108.5,641.4,30.6,15.8,-2.3,174.7],speed=75)  
timed_sleep(0.5)
# second common point (for both insert and tap )


# arm.open_lite6_gripper()
# timed_sleep(1)
move_to_cartesian([108.5,641.4,68.3,15.8,-2.3,174.7],speed=25)  
arm.open_lite6_gripper()
timed_sleep(1)
move_to_cartesian([108.5,641.4,130.7,15.8,-2.3,174.7],speed=25)  
timed_sleep(0.5)
#card rack 1 (tap and insert)
arm.close_lite6_gripper()
timed_sleep(1.5)
move_to_cartesian([108.5,641.4,68.3,15.8,-2.3,174.7],speed=25) 
# move_to_cartesian([108.5,641.4,30.6,15.8,-2.3,174.7],speed=25)  
timed_sleep(0.5)

# card pickup end


move_to_cartesian([124.3,617.3,-132.2,12.1,-3,177.2],speed=75)  
timed_sleep(0.5) #top most point for tap
# move_to_cartesian([59,608.9,-6.4,6.7,1,173.1])  
# timed_sleep(1.5)

move_to_cartesian([235.7,587.5,-106.5,-93.1,21.9,-92.8],speed=75)  
timed_sleep(1.5) #second top spot before tap
move_to_cartesian([269.3,546.5,51.7,-67.6,20.3,-96.7])
 #tap positon
move_to_cartesian([241.9,546.5,51.7,-67.6,20.3,-98.7])
timed_sleep(8) #tap positon

move_to_cartesian([235.7,587.5,-106.5,-93.1,21.9,-92.8],speed=55)  
timed_sleep(1.5) #second top spot before tap
move_to_cartesian([124.3,617.3,-132.2,12.1,-3,177.2],speed=75)  

timed_sleep(0.5) #top most point for tap
#move_to_cartesian([124.4,617.3,-50,12.1,-3,177.2],speed=65) 
# move_to_cartesian([124.4,617.3,0,12.1,-3,177.2],speed=65) 
# move_to_cartesian([124.4,617.3,24.3,12.1,-3,177.2],speed=65)  
timed_sleep(0.5) #back to 2nd common spot

#card putdown start
#move_to_cartesian([59,608.9,-6.4,6.7,1,173.1],speed=75)  

# move_to_cartesian([108.5,641.4,30.6,15.8,-2.3,174.7],speed=75)  
timed_sleep(0.5)

move_to_cartesian([108.5,641.4,68.3,15.8,-2.3,174.7],speed=25)  
move_to_cartesian([108.5,641.4,130.7,15.8,-2.3,174.7],speed=25)
timed_sleep(0.5)

arm.open_lite6_gripper()
timed_sleep(1)

# move_to_cartesian([108.5,641.4,68.3,15.8,-2.3,174.7],speed=25) 
timed_sleep(0.5)

move_to_cartesian([108.5,641.4,68.3,15.8,-2.3,174.7],speed=25)
arm.close_lite6_gripper()
timed_sleep(1.5)

move_to_cartesian([59,608.9,-6.4,6.7,1,173.1],speed=75)  

#card putdown end