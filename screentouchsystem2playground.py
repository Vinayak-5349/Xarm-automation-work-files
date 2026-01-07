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
arm.set_collision_sensitivity(5, wait=True)
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

move_to_cartesian([59, 608.9, -6.4, 6.7, 1, 173.1], speed=95)
move_to_cartesian([72.5, 720.7, -97.2, 34.5, 0.5, 173.9], speed=95)
move_to_cartesian([281.4, 590.9, -168.9, -49.2, 4.5, -65], speed=95)
move_to_cartesian([307.1, 555.7, -23.2, -0.7, 18.2, -93.5], speed=90)
# # food

# move_to_cartesian([349,596.7,28.4,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([349,593.7,37.4,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([349,596.7,28.4,-0.7,18.2,-93.5],speed=25)

# #cash 

# move_to_cartesian([269.8,601.2,29.3,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([269.7,598.7,36.9,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([269.8,601.2,29.3,-0.7,18.2,-93.5],speed=25)
  



# #yes

# move_to_cartesian([269.8,601.2,29.3,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([269.7,598.7,36.9,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([269.8,601.2,29.3,-0.7,18.2,-93.5],speed=25)

# #no

# move_to_cartesian([349,596.7,28.4,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([349,593.7,37.4,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([349,596.7,28.4,-0.7,18.2,-93.5],speed=25)





# #other
# move_to_cartesian([257.3,606.4,30.9,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([257.2,603.8,38.9,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([257.3,606.4,30.9,-0.7,18.2,-93.5],speed=25)





# #30
# move_to_cartesian([258.3,630.5,38.9,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([258.2,627.2,48,-0.7,18.2,-93.5],speed=25)

# move_to_cartesian([258.3,630.5,38.9,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([258.2,627.2,48,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([258.3,630.5,38.9,-0.7,18.2,-93.5],speed=25)


# #20
# move_to_cartesian([311.8,627,38.1,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([311.7,623.6,49.1,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([311.8,627,38.1,-0.7,18.2,-93.5],speed=25)





# #10
# move_to_cartesian([366.2,623.9,37.5,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([366.1,620.3,49.3,-0.7,18.2,-93.5],speed=65)
# move_to_cartesian([361.1,620.1,49.2,-0.7,18.2,-93.5],speed=65)

# move_to_cartesian([366.2,623.9,37.5,-0.7,18.2,-93.5],speed=65)




# #40

# move_to_cartesian([364.8,601,29.9,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([364.7,597.7,43,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([364.8,601,29.9,-0.7,18.2,-93.5],speed=25)







# #50
# move_to_cartesian([311,603.6,30.4,-0.7,18.2,-93.5],speed=25)
# move_to_cartesian([310.9,600.8,43,-0.7,18.2,-93.5],speed=25)

# move_to_cartesian([311,603.6,30.4,-0.7,18.2,-93.5],speed=25)










move_to_cartesian([307.1, 555.7, -23.2, -0.7, 18.2, -93.5], speed=60)
move_to_cartesian([281.4, 590.9, -168.9, -49.2, 4.5, -65], speed=75)
move_to_cartesian([72.5, 720.7, -97.2, 34.5, 0.5, 173.9], speed=75)
move_to_cartesian([59, 608.9, -6.4, 6.7, 1, 173.1], speed=75)