import time
import json
import logging
from xarm.wrapper import XArmAPI

# === Setup Logger ===
logging.basicConfig(
    filename='robot_action.log',
    level=logging.INFO,
    format='%(asctime)s [RECORD] %(message)s',
)

# === Connect to Robot Arm ===
xarm_ip = "192.168.1.159"
arm = XArmAPI(xarm_ip)
arm.connect()
arm.clean_error()
arm.clean_warn()
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(0)

RECORD_FILE = "insert_system2_rack2_down.json"
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
        (-360, 360),   # J1
        (-120, 120),   # J2
        (-135, 135),   # J3
        (-360, 360),   # J4
        (-120, 120),   # J5
        (-360, 360),   # J6
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
    logging.info("Started recording: INSERT action, Rack 1")
    recorded_sequence["current"] = []

    move_to_cartesian([59,608.9,-6.4,6.7,1,173.1], speed=95)
    move_to_cartesian([293.7,393.8,-149.2,69.7,1.2,175],speed=50) 
    move_to_cartesian([284.6,339.5,56.7,69.7,1.2,175],speed=50) 
      
    open_gripper()     
    move_along_tool_z(40)
    close_gripper()
    timed_sleep(1)
    move_along_tool_z(-40)

    move_to_cartesian([284.6,339.5,56.7,69.7,1.2,175],speed=50)
    move_to_cartesian([284.9,341.6,51.1,69.7,1.2,175],speed=50)   
    move_to_cartesian([283.2,307.4,39.8,69.7,1.2,175], speed=95) 
    move_to_cartesian([242.9,426.9,-209.3,26.2,-23.9,104.6], speed=95)
    move_to_cartesian([124.3,617.3,-132.2,12.1,-3,177.2], speed=95) 




    move_to_cartesian([115.8,650.5,45.5,17.6,0.7,175], speed=95)  
    move_to_cartesian([117.2,678.5,133.9,17.6,0.7,175], speed=95) 
    open_gripper()
    timed_sleep(0.5)
    move_to_cartesian([117,652.6,45.1,17.6,0.7,175], speed=95)  
    close_gripper()
    move_to_cartesian([59,608.9,-6.4,6.7,1,173.1], speed=95)  


















    # timed_sleep(1)

    

    logging.info("Completed recording: INSERT action, Rack 1")
    return recorded_sequence["current"]

# === MAIN EXECUTION ===
def main():
    recorded_sequence["current"] = []  
    step_data = {}
    step_data["insert_system1_rack2_down"] = insert_rack1()

    with open(RECORD_FILE, "w") as f:
        json.dump(step_data, f, indent=4)

    logging.info(f"Saved all recorded steps to {RECORD_FILE}")

if __name__ == "__main__":
    main()
