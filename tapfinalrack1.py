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

RECORD_FILE = "RECORDED_ACTIONS1.json"
recorded_sequence = {}

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
    logging.info(f"Slept for {duration} sec")

# === Move using Cartesian and record ===
def move_to_cartesian(pos, speed):
    status, joints = arm.get_inverse_kinematics(pos, input_is_radian=False, return_is_radian=False)
    if status != 0 or not joints:
        logging.error(f"Inverse kinematics failed for position: {pos}")
        return
    joints = [float(j) for j in joints[:6]]
    timed_call("move", {"joints": joints, "speed": speed}, arm.set_servo_angle,
               angle=joints, speed=speed, is_radian=False, wait=True)

# === Wrapper for Gripper Open/Close ===
def open_gripper():
    timed_call("gripper_open", {}, lambda: arm.open_lite6_gripper())

def close_gripper():
    timed_call("gripper_close", {}, lambda: arm.close_lite6_gripper())

# === Record Tap Action for Rack 1 ===
def tap_rack1():
    logging.info("Started recording: TAP action, Rack 1")
    recorded_sequence["current"] = []

    move_to_cartesian([59, 608.9, -6.4, 6.7, 1, 173.1], speed=75)
    timed_sleep(0)

    move_to_cartesian([108.5, 641.4, 68.3, 15.8, -2.3, 174.7], speed=75)
    open_gripper()
    timed_sleep(0.5)

    # move_to_cartesian([108.5, 641.4, 130.7, 15.8, -2.3, 174.7], speed=25)
    move_to_cartesian([113,641.4,132.2,15.6,-0.3,174.7],speed=25)  
    timed_sleep(0.5)
    close_gripper()
    timed_sleep(0.5)

    move_to_cartesian([108.5, 641.4, 68.3, 15.8, -2.3, 174.7], speed=25)
    timed_sleep(0.5)

    move_to_cartesian([124.3, 617.3, -132.2, 12.1, -3, 177.2], speed=75)
    timed_sleep(0)

    move_to_cartesian([235.7, 587.5, -106.5, -93.1, 21.9, -92.8], speed=75)
    timed_sleep(0)

    move_to_cartesian([269.3, 546.5, 51.7, -67.6, 20.3, -96.7], speed=75)
    timed_sleep(1.5)
    move_to_cartesian([241.9,546.5,51.7,-67.6,20.3,-98.7],speed=25)
    timed_sleep(8)
    move_to_cartesian([235.7, 587.5, -106.5, -93.1, 21.9, -92.8], speed=55)
    timed_sleep(0)

    move_to_cartesian([124.3, 617.3, -132.2, 12.1, -3, 177.2], speed=75)
    timed_sleep(0)

    move_to_cartesian([108.5, 641.4, 68.3, 15.8, -2.3, 174.7], speed=25)
    # move_to_cartesian([108.5, 641.4, 130.7, 15.8, -2.3, 174.7], speed=25)
    move_to_cartesian([113,641.4,132.2,15.6,-0.3,174.7],speed=25)  
    timed_sleep(0.5)

    open_gripper()
    timed_sleep(0.5)

    move_to_cartesian([108.5, 641.4, 68.3, 15.8, -2.3, 174.7], speed=75)
    close_gripper()
    timed_sleep(0.5)

    move_to_cartesian([59, 608.9, -6.4, 6.7, 1, 173.1], speed=75)

    logging.info("Completed recording: TAP action, Rack 1")
    return recorded_sequence["current"]

# === MAIN EXECUTION ===
def main():
    recorded_sequence["current"] = []  
    step_data = {}
    step_data["tap_system1_rack1"] = tap_rack1()

    with open(RECORD_FILE, "w") as f:
        json.dump(step_data, f, indent=4)

    logging.info(f"Saved all recorded steps to {RECORD_FILE}")

if __name__ == "__main__":
    main()
