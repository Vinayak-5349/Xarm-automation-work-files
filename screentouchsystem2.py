import time
import json
from xarm.wrapper import XArmAPI

xarm_ip = "192.168.1.159"
arm = XArmAPI(xarm_ip)
arm.connect()
arm.clean_error()
arm.clean_warn()
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(0)

PIN_STEP_FILE = "Screen_Touch_System2.json"
recorded_sequence = {}

def record_step(step_type, data, delay):
    step = {"type": step_type, "delay": delay}
    step.update(data)
    recorded_sequence["current"].append(step)

def timed_call(step_type, data, func, *args, **kwargs):
    start = time.time()
    func(*args, **kwargs)
    delay = time.time() - start
    record_step(step_type, data, delay)

def timed_sleep(duration):
    time.sleep(duration)
    record_step("sleep", {"duration": duration}, duration)

def move_to_cartesian(pos, speed):
    status, joints = arm.get_inverse_kinematics(pos, input_is_radian=False, return_is_radian=False)
    if status == 0 and joints:
        joints = [float(j) for j in joints[:6]]
        timed_call("move", {"joints": joints, "speed": speed}, arm.set_servo_angle, angle=joints, speed=speed, is_radian=False, wait=True)

def record_entry():
    recorded_sequence["current"] = []
    move_to_cartesian([59, 608.9, -6.4, 6.7, 1, 173.1], speed=75)
    move_to_cartesian([72.5, 720.7, -97.2, 34.5, 0.5, 173.9], speed=75)
    move_to_cartesian([281.4, 590.9, -168.9, -49.2, 4.5, -65], speed=75)
    move_to_cartesian([307.1, 555.7, -23.2, -0.7, 18.2, -93.5], speed=60)
    return recorded_sequence["current"]

def record_exit():
    recorded_sequence["current"] = []
    move_to_cartesian([307.1, 555.7, -23.2, -0.7, 18.2, -93.5], speed=60)
    move_to_cartesian([281.4, 590.9, -168.9, -49.2, 4.5, -65], speed=75)
    move_to_cartesian([72.5, 720.7, -97.2, 34.5, 0.5, 173.9], speed=75)
    move_to_cartesian([59, 608.9, -6.4, 6.7, 1, 173.1], speed=75)
    return recorded_sequence["current"]

def record_button(name, steps):
    recorded_sequence["current"] = []
    for pos in steps:
        move_to_cartesian(pos, pos[-1])
        if pos[-1] == 10:
            timed_sleep(0.2)
    return recorded_sequence["current"]

def main():
    step_data = {}

    print("[INFO] Recording ENTRY path...")
    step_data["entry"] = record_entry()

    print("[INFO] Recording BUTTONS...")
    button_coords = {
    "food": [
        [349, 596.7, 28.4, -0.7, 18.2, -93.5, 25],
        [349, 593.7, 37.4, -0.7, 18.2, -93.5, 25],
        [349, 596.7, 28.4, -0.7, 18.2, -93.5, 25]
    ],

    "cash": [
        [269.8, 601.2, 29.3, -0.7, 18.2, -93.5, 25],
        [269.7, 598.7, 36.9, -0.7, 18.2, -93.5, 25],
        [269.8, 601.2, 29.3, -0.7, 18.2, -93.5, 25]
    ],

    "yes": [
        [269.8, 601.2, 29.3, -0.7, 18.2, -93.5, 25],
        [269.7, 598.7, 36.9, -0.7, 18.2, -93.5, 25],
        [269.8, 601.2, 29.3, -0.7, 18.2, -93.5, 25]
    ],

    "no": [
        [349, 596.7, 28.4, -0.7, 18.2, -93.5, 25],
        [349, 593.7, 37.4, -0.7, 18.2, -93.5, 25],
        [349, 596.7, 28.4, -0.7, 18.2, -93.5, 25]
    ],

    "other": [
        [257.3, 606.4, 30.9, -0.7, 18.2, -93.5, 25],
        [257.2, 603.8, 38.9, -0.7, 18.2, -93.5, 25],
        [257.3, 606.4, 30.9, -0.7, 18.2, -93.5, 25]
    ],

    "30": [
        [258.3, 630.5, 38.9, -0.7, 18.2, -93.5, 25],
        [258.2, 627.5, 48.1, -0.7, 18.2, -93.5, 25],
        [258.3, 630.5, 38.9, -0.7, 18.2, -93.5, 25]
    ],

    "20": [
        [311.8, 627, 38.1, -0.7, 18.2, -93.5, 25],
        [311.7, 623.6, 48.3, -0.7, 18.2, -93.5, 25],
        [311.8, 627, 38.1, -0.7, 18.2, -93.5, 25]
    ],

    "10": [
        [366.2, 623.9, 37.5, -0.7, 18.2, -93.5, 25],
        [366.1, 620.3, 48.4, -0.7, 18.2, -93.5, 25],
        [366.2, 623.9, 37.5, -0.7, 18.2, -93.5, 25]
    ],

    "40": [
        [364.8, 601, 29.9, -0.7, 18.2, -93.5, 25],
        [364.7, 597.7, 39.9, -0.7, 18.2, -93.5, 25],
        [364.8, 601, 29.9, -0.7, 18.2, -93.5, 25]
    ],

    "50": [
        [311, 603.6, 30.4, -0.7, 18.2, -93.5, 25],
        [310.9, 600.8, 39, -0.7, 18.2, -93.5, 25],
        [311, 603.6, 30.4, -0.7, 18.2, -93.5, 25]
    ]
}



    step_data["buttons"] = {}
    for key, steps in button_coords.items():
        print(f"[INFO] Recording button '{key}'...")
        step_data["buttons"][key] = record_button(key, steps)

    print("[INFO] Recording EXIT path...")
    step_data["exit"] = record_exit()

    print(f"[INFO] Saving recorded steps to {PIN_STEP_FILE}...")
    with open(PIN_STEP_FILE, "w") as f:
        json.dump(step_data, f, indent=4)

    print("✅ All pin steps recorded and saved successfully.")

if __name__ == "__main__":
    main()
