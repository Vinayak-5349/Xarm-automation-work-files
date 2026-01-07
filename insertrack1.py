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
# def move_to_cartesian(cartesian_position, speed=20):
#     status_code, joint_angles = arm.get_inverse_kinematics(cartesian_position, input_is_radian=False, return_is_radian=False)
#     if status_code != 0 or not joint_angles:
#         print("Failed to calculate inverse kinematics.")
#         return
#     joint_angles = [float(angle) for angle in joint_angles[:6]]
#     arm.set_servo_angle(angle=joint_angles, speed=speed, is_radian=False, wait=True)
def move_to_cartesian(cartesian_position, speed=20):
    status_code, joint_angles = arm.get_inverse_kinematics(
        cartesian_position, input_is_radian=False, return_is_radian=False
    )
    if status_code != 0 or not joint_angles:
        print("Failed to calculate inverse kinematics.")
        return

    # Convert to floats
    joint_angles = [float(angle) for angle in joint_angles[:6]]

    # Get current joint positions
    _, current_angles = arm.get_servo_angle(is_radian=False)

    if current_angles:
        # Fix discontinuity: ensure smallest rotation on each joint
        for i in range(6):
            diff = joint_angles[i] - current_angles[i]
            if diff > 180:
                joint_angles[i] -= 360
            elif diff < -180:
                joint_angles[i] += 360

    # Send corrected joint angles
    arm.set_servo_angle(angle=joint_angles, speed=speed, is_radian=False, wait=True)



move_to_cartesian([59,608.9,-6.4,6.7,1,173.1],speed=75)  
# timed_sleep(1.5)
# fist common point (for both swipe,tap and insert )



timed_sleep(0.5)
# second common point (for both insert and tap )

move_to_cartesian([108.5,641.4,68.3,15.8,-2.3,174.7],speed=25)  
arm.open_lite6_gripper()
timed_sleep(1)
# move_to_cartesian([108.5,641.4,130.7,15.8,-2.3,174.7],speed=25)  
move_to_cartesian([113,641.4,132.2,15.6,-0.3,174.7],speed=25)  
timed_sleep(0.5)
#card rack 1 (tap and insert)
arm.close_lite6_gripper()
timed_sleep(1.5)
move_to_cartesian([108.5,641.4,68.3,15.8,-2.3,174.7],speed=25) 
# move_to_cartesian([108.5,641.4,30.6,15.8,-2.3,174.7],speed=25)  
timed_sleep(0.5)

# # card pickup end


move_to_cartesian([124.3,617.3,-132.2,12.1,-3,177.2],speed=75) 
# move_to_cartesian([178.4,582,-143.9,12.7,-9.4,160.6],speed=75) 
# move_to_cartesian([233.1,503,-172.5,17.3,-18.1,134.1],speed=75) 
# move_to_cartesian([244.9,447.9,-193.4,22,-22,117.4],speed=75) 

#insert first point
move_to_cartesian([242.9,426.9,-209.3,26.2,-23.9,104.6],speed=35)  
#insert second
move_to_cartesian([280.8,374.2,-101.4,69.7,-102,177.8],speed=35)  
#insert 3rd
move_to_cartesian([286.3,306.9,40.5,69.7,3.7,176],speed=35)  
#insert 1st
move_to_cartesian([286.3,340.7,46.6,68.4,0,175.7],speed=5) 
#2nd
move_to_cartesian([286.3,340.7,51.9,68.4,0,175.7],speed=5) 
#3rd
move_to_cartesian([286.3,340.1,53,68.4,0,175.7],speed=5) 
timed_sleep(2)
move_to_cartesian([286.3,356.6,56.7,68.4,0,175.7],speed=5) 
move_to_cartesian([286.3,378.1,66.1,68.4,0,175.4],speed=4) 
timed_sleep(7)
move_to_cartesian([286.3,356.6,56.7,68.4,0,175.7],speed=3) 
move_to_cartesian([286.3,340.1,53,68.4,0,175.7],speed=3) 



move_to_cartesian([286.3,340.7,51.9,68.4,0,175.7],speed=5) 

move_to_cartesian([286.3,306.9,40.5,69.7,3.7,176],speed=35)  

move_to_cartesian([280.8,374.2,-101.4,69.7,-102,177.8],speed=35)  
 
move_to_cartesian([242.9,426.9,-209.3,26.2,-23.9,104.6],speed=35)  

move_to_cartesian([124.3,617.3,-132.2,12.1,-3,177.2],speed=75) 

#card putdown start
#move_to_cartesian([59,608.9,-6.4,6.7,1,173.1],speed=75)  

# move_to_cartesian([108.5,641.4,30.6,15.8,-2.3,174.7],speed=75)  
timed_sleep(0.5)

move_to_cartesian([108.5,641.4,68.3,15.8,-2.3,174.7],speed=25)  
move_to_cartesian([113,641.4,132.2,15.6,-0.3,174.7],speed=25)  
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