import time
from xarm.wrapper import XArmAPI

xarm_ip = "192.168.1.183"
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
#instial pos
move_to_cartesian([-12.2,246,170.6,-152.3,0.7,1.5],speed=95)  
move_to_cartesian([-327.3,152.8,266.4,-179.3,-0.3,87.9],speed=95)  
move_to_cartesian([-327.3,152.8,126.1,-179.3,-0.3,87.9],speed=95) 
# move_to_cartesian([307.1,555.7,-23.2,-0.7,18.2,-93.5],speed=60) 


# 1 start 
#common point
move_to_cartesian([-350.5,172.3,110.3,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-350.5,172.4,104.2,-179.3,-0.3,87.9],speed=50)
timed_sleep(0.2)
move_to_cartesian([-350.5,172.3,110.3,-179.3,-0.3,87.9],speed=50)  
# # # 1 end
# # #2 start
# # # common point for pin entry
move_to_cartesian([-330.1,172.8,110.1,-179.3,-0.3,87.9],speed=50)   
move_to_cartesian([-330.2,171.8,103.6,-179.3,-0.3,87.9],speed=50) 
timed_sleep(0.2)
move_to_cartesian([-330.1,172.8,110.1,-179.3,-0.3,87.9],speed=50)  
# # #2 end
# # #3 start
move_to_cartesian([-309,173,109.8,-179.3,-0.3,87.9],speed=50)  
move_to_cartesian([-309.1,172.7,104.1,-179.3,-0.3,87.9],speed=50)    
timed_sleep(0.2)
move_to_cartesian([-309,173,109.8,-179.3,-0.3,87.9],speed=50)   
# # #3 end
# # #4 start
move_to_cartesian([-350.5,162.5,110.2,-179.3,-0.3,87.9],speed=50) 
move_to_cartesian([-350.6,162.6,103.7,-179.3,-0.3,87.9],speed=50) 
timed_sleep(0.2)
move_to_cartesian([-350.5,162.5,110.2,-179.3,-0.3,87.9],speed=50) 
# # 4 end 
# # 5start
move_to_cartesian([-329.5,162.8,109.9,-179.3,-0.3,87.9],speed=50)  
move_to_cartesian([-329.6,161.8,103.9,-179.3,-0.3,87.9],speed=50) 
timed_sleep(0.2)
move_to_cartesian([-329.5,162.8,109.9,-179.3,-0.3,87.9],speed=50) 
# # 5 end 
# # 6 start 
move_to_cartesian([-308.7,163,109.7,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-308.8,162.1,103.7,-179.3,-0.3,87.9],speed=50) 
timed_sleep(0.2)
move_to_cartesian([-308.7,163,109.7,-179.3,-0.3,87.9],speed=50)

# # 6 end 
# # 7 start 
move_to_cartesian([-348,153.4,110.1,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-349.1,152.5,103.1,-179.3,-0.3,87.9],speed=50)
timed_sleep(0.2)
move_to_cartesian([-348,153.4,110.1,-179.3,-0.3,87.9],speed=50)
# # 7 end 
# # 8 start 
move_to_cartesian([-327.3,152.7,109.8,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-327.7,152.7,103.8,-179.3,-0.3,87.9],speed=50)
timed_sleep(0.2)
move_to_cartesian([-327.3,152.7,109.8,-179.3,-0.3,87.9],speed=50)
# # 8 end
# # 9 start 
move_to_cartesian([-309.1,152,109.6,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-309.2,152,103.6,-179.3,-0.3,87.9],speed=50)
timed_sleep(0.2)
move_to_cartesian([-309.1,152,109.6,-179.3,-0.3,87.9],speed=50)
# # 9 end 
# # 0 start

move_to_cartesian([-327.1,141.7,109.8,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-327.2,141.7,103.8,-179.3,-0.3,87.9],speed=50)
timed_sleep(0.2)
move_to_cartesian([-327.1,141.7,109.8,-179.3,-0.3,87.9],speed=50)
# # 0 end

# # backspace
move_to_cartesian([-327.5,131,110.7,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-327.6,131,103.7,-179.3,-0.3,87.9],speed=50)
timed_sleep(0.2)
move_to_cartesian([-327.5,131,110.7,-179.3,-0.3,87.9],speed=50)
# # backspace


# # ok start
move_to_cartesian([-309.6,132.3,110.5,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-309.7,132.4,103,-179.3,-0.3,87.9],speed=50)
timed_sleep(0.2)
move_to_cartesian([-309.6,132.3,110.5,-179.3,-0.3,87.9],speed=50)
# # ok ends

## cancel start
move_to_cartesian([-351.2,132.3,111,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-351.3,132.3,103.3,-179.3,-0.3,87.9],speed=50)
timed_sleep(0.2)
move_to_cartesian([-351.2,132.3,111,-179.3,-0.3,87.9],speed=50)

#food

move_to_cartesian([-366.8,212.7,121.4,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-367,212.8,109.4,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-366.8,212.7,121.4,-179.3,-0.3,87.9],speed=50)
#food

#cash
move_to_cartesian([-285.2,209.7,120.4,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-285.3,209.8,107.4,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-285.2,209.7,120.4,-179.3,-0.3,87.9],speed=25)

#cash
#no
move_to_cartesian([-285.2,209.7,120.4,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-285.3,209.8,107.4,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-285.2,209.7,120.4,-179.3,-0.3,87.9],speed=25)

#no


#yes

move_to_cartesian([-366.8,212.7,121.4,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-367,212.8,109.4,-179.3,-0.3,87.9],speed=50)
move_to_cartesian([-366.8,212.7,121.4,-179.3,-0.3,87.9],speed=50)
#yes
#other
move_to_cartesian([-277.8,215.4,120.3,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-278,215.5,109.3,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-277.8,215.4,120.3,-179.3,-0.3,87.9],speed=25)
#other

#30
move_to_cartesian([-276.9,240.2,120.5,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-277.1,240.2,109.5,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-276.9,240.2,120.5,-179.3,-0.3,87.9],speed=25)
#30


#10
move_to_cartesian([-363.9,243.4,121.5,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-364,243.4,109,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-363.9,243.4,121.5,-179.3,-0.3,87.9],speed=25)
#10

#20
move_to_cartesian([-333.6,242.2,121.2,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-333.7,242.3,109.2,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-333.6,242.2,121.2,-179.3,-0.3,87.9],speed=25)
#20

#50
move_to_cartesian([-334.6,217.3,121.6,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-334.6,217.4,109.6,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-334.6,217.3,121.6,-179.3,-0.3,87.9],speed=25)
#50

#40
move_to_cartesian([-366.1,218.2,121.6,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-366.3,218.3,109.6,-179.3,-0.3,87.9],speed=25)
move_to_cartesian([-366.1,218.2,121.6,-179.3,-0.3,87.9],speed=25)
#40





#exit path
move_to_cartesian([-327.3,152.8,126.1,-179.3,-0.3,87.9],speed=95) 
move_to_cartesian([-327.3,152.8,266.4,-179.3,-0.3,87.9],speed=95)

move_to_cartesian([-12.2,246,170.6,-152.3,0.7,1.5],speed=95) 
