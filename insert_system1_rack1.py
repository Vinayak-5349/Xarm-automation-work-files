import time
import json
import logging
from xarm.wrapper import XArmAPI

# === Setup Logger ===
logging.basicConfig(
    filename='robot_action_swipe.log',
    level=logging.INFO,
    format='%(asctime)s [RECORD] %(message)s',
)

# === Connect to Robot Arm ===
xarm_ip = "192.168.1.183"
arm = XArmAPI(xarm_ip)
arm.connect()
arm.clean_error()
arm.clean_warn()
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(0)

RECORD_FILE = "insert_system1_rack1(4).json"
recorded_sequence = {}
import traceback
import inspect

# Error code mapping for xArm (you can expand this list as needed)
ERROR_CODES = {
    -8: "Out of joint range",
    2: "I/O error (e.g., tgpio not available)",
    14: "IK calculation failed",
    0: "Success"
}

import traceback
import inspect

# Error code mapping for xArm (extend as needed)
ERROR_CODES = {
    -8: "Out of joint range",
    2: "I/O error",
    14: "IK calculation failed",
    0: "Success"
}
# === Record step into memory ===
def record_step(step_type, data, delay):
    if "current" not in recorded_sequence:
        recorded_sequence["current"] = []
    step = {"type": step_type, "delay": delay}
    step.update(data)
    recorded_sequence["current"].append(step)
    logging.info(f"Recorded step: {step}")

# === Wrapper for recording timed actions ===
def timed_call(step_type, data, func, *args, **kwargs):
    start = time.time()
    func(*args, **kwargs)
    delay = time.time() - start
    record_step(step_type, data, delay)

# === Wrapper for sleep ===
def timed_sleep(duration):
    time.sleep(duration)
    record_step("sleep", {"duration": duration}, duration)

# === Move using Cartesian and record ===
def log_error(code, msg=""):
    if code == 0:
        return
    frame = inspect.currentframe().f_back
    filename = frame.f_code.co_filename
    line_no = frame.f_lineno
    desc = ERROR_CODES.get(code, "Unknown error")
    print(f"[ERROR] Code {code} ({desc}) at {filename}:{line_no} {msg}")
    traceback.print_stack(limit=2)

import numpy as np
from scipy.interpolate import CubicSpline

# Your waypoints (X, Y, Z only for simplicity here)
points = [
    [107.6,629.3,152.7],
    [107.6,609.8,144.7],
    [107.6,592.0,140.0],
    [107.6,578.4,132.4],
    [107.6,561.6,126.4],
    [107.6,553.6,124.4],
    [107.6,539.8,119.4],
    [107.6,524.7,112.9],
    [107.6,503.2,104.4],
    [107.6,493.7,101.9],
]

points = np.array(points)
t = np.arange(len(points))

# Fit spline for each axis
spl_x = CubicSpline(t, points[:,0])
spl_y = CubicSpline(t, points[:,1])
spl_z = CubicSpline(t, points[:,2])

# Generate 50 smooth intermediate points
t_new = np.linspace(0, len(points)-1, 50)
smooth_points = np.stack([spl_x(t_new), spl_y(t_new), spl_z(t_new)], axis=1)
def move_to_cartesian(cartesian_position, speed=20, comment=None):
    """
    Move robot to a Cartesian position with IK + shortest path + joint limit check,
    while recording the move into the JSON log.
    """
    if comment:
        print(f"--- {comment} ---")

    # Get IK solution
    status_code, joint_angles = arm.get_inverse_kinematics(
        cartesian_position, input_is_radian=False, return_is_radian=False
    )
    if status_code != 0 or not joint_angles:
        log_error(status_code, "while calculating IK")
        logging.error(f"Inverse kinematics failed for position: {cartesian_position}")
        return False

    # Convert to float and only take first 6 axes
    joint_angles = [float(angle) for angle in joint_angles[:6]]

    # Get current joint angles (for shortest path correction)
    _, current_angles = arm.get_servo_angle(is_radian=False)
    if current_angles:
        for i in range(6):
            diff = joint_angles[i] - current_angles[i]
            if diff > 180:
                joint_angles[i] -= 360
            elif diff < -180:
                joint_angles[i] += 360

    # --- SAFETY CHECK for joint limits (in degrees) ---
    joint_limits_deg = [
        (-355, 355),   # J1
        (-145, 145),   # J2
        (2, 355) ,  # J3
        (-355, 355),   # J4
        (-119, 119),   # J5
        (-355, 355),   # J6
    ]

    for i, angle in enumerate(joint_angles):
        low, high = joint_limits_deg[i]
        if angle < low or angle > high:
            print(f"[WARNING] Joint {i+1} out of range ({angle:.2f}°). Skipping move.")
            return False

    # Send move command WITH RECORDING
    def _do_move():
        return arm.set_servo_angle(angle=joint_angles, speed=speed, is_radian=False, wait=True)

    # timed_call will measure delay + record step automatically
    timed_call("move", {"joints": joint_angles, "speed": speed}, _do_move)

    print("[OK] Move successful")
    return True
def move_along_tool_z(dz, speed=10):
    timed_call("tool_move", {"dx": 0, "dy": 0, "dz": dz, "speed": speed},
               arm.set_tool_position, 0, 0, dz, 0, 0, 0, speed=speed, wait=True)


# === Wrapper for Gripper Open/Close ===
def open_gripper():
    timed_call("gripper_open", {}, lambda: arm.open_lite6_gripper())

def close_gripper():
    timed_call("gripper_close", {}, lambda: arm.close_lite6_gripper())

# === INSERT SEQUENCE RECORDING ===
def insert_rack1():
    logging.info("Started recording: SWIPE action, Rack 1")
    recorded_sequence["current"] = []


    #pick up start

 
 
    
 
 
 
    move_to_cartesian([-31.1,256.7,194.1,-140.8,2.1,-0.3],speed=95)  
    
    move_to_cartesian([56.3,292.4,126.3,-143.5,-0.8,0.9],speed=95)  
    open_gripper()
    timed_sleep(0.5)
    move_to_cartesian([56.4,350.8,47.4,-143.5,-0.8,0.9],speed=75)  
    close_gripper()
    timed_sleep(0.5)
    move_to_cartesian([56.3,292.4,126.3,-143.5,-0.8,0.9],speed=95)
    
    
    move_to_cartesian([-31.1,256.7,194.1,-140.8,2.1,-0.3],speed=95)  
    
    move_to_cartesian([-3.9,334.9,277.3,-91.5,0.8,-3],speed=95)
    move_to_cartesian([-72.1,327.3,277.1,-91.1,-0.2,-1.9],speed=95)
    move_to_cartesian([-336,10.2,276.5,-91.7,1.5,84.7],speed=95)
    move_to_cartesian([-335.1,27.8,94.5,-91.1,-0.2,-1.9],speed=95)
    move_to_cartesian([-340.1,63.3,89,-91.1,-0.2,-1.9],speed=75)
    move_to_cartesian([-340.1,63.2,86,-91.1,-0.2,-1.9],speed=75)
    timed_sleep(0.5)
    move_along_tool_z(40,speed=20)
    timed_sleep(4)
    move_along_tool_z(-40,speed=20)
    move_to_cartesian([-340.1,63.2,86,-91.1,-0.2,-1.9],speed=75)
    move_to_cartesian([-340.1,63.3,89,-91.1,-0.2,-1.9],speed=75)    
    move_to_cartesian([-335.1,27.8,94.5,-91.1,-0.2,-1.9],speed=95)
    move_to_cartesian([-335.1,31.9,264.4,-91.1,-0.2,-1.9],speed=95)

    # move_to_cartesian([-336,10.2,276.5,-91.7,1.5,84.7],speed=75)
    move_to_cartesian([-72.1,327.3,277.1,-91.1,-0.2,-1.9],speed=95)
    # move_to_cartesian([-3.9,334.9,277.3,-91.5,0.8,-3],speed=75)
    move_to_cartesian([56.3,292.4,126.3,-143.5,-0.8,0.9],speed=95)
    move_to_cartesian([56.4,350.8,47.4,-143.5,-0.8,0.9],speed=75)  
    open_gripper()
    timed_sleep(0.5)
    move_to_cartesian([56.3,292.4,126.3,-143.5,-0.8,0.9],speed=95)
    close_gripper()
    move_to_cartesian([-31.1,256.7,194.1,-140.8,2.1,-0.3],speed=95) 







    return recorded_sequence["current"]  # return the steps

# === MAIN EXECUTION ===
def main():
    recorded_sequence["current"] = []  
    step_data = {}
    step_data["insert_system1_rack1"] = insert_rack1()

    with open(RECORD_FILE, "w") as f:
        json.dump(step_data, f, indent=4)

    logging.info(f"Saved all recorded steps to {RECORD_FILE}")

if __name__ == "__main__":
    main()
