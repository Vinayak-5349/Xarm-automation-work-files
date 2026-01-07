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

PIN_STEP_FILE = "PIN_STEPS.json"
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
    "1": [[332.7, 560.6, 27.2, 1.1, 19.6, -93.7, 50], [332.7, 559.1, 31.2, 1.1, 19.6, -93.7, 10], [332.7, 560.6, 27.2, 1.1, 19.6, -93.7, 50]],
    "2": [[315.1, 557.1, 26.7, 3.4, 16.7, -93, 50], [315.1, 555.6, 30.3, 3.4, 16.7, -93, 10], [315.1, 557.1, 26.7, 3.4, 16.7, -93, 50]],
    "3": [[291.8, 561.2, 26.7, 1.2, 18.6, -93.6, 50], [291.8, 561.2, 31.2, 1.1, 19.6, -93.6, 10], [291.8, 561.2, 26.7, 1.2, 18.6, -93.6, 50]],
    "4": [[332, 549.3, 22.6, 0.2, 19.2, -96.5, 50], [332, 549.3, 27.1, 0.1, 20.2, -96.5, 10], [332, 549.3, 22.6, 0.2, 19.2, -96.5, 50]],
    "5": [[311.5, 550.3, 22.6, 0.2, 19.2, -96.5, 50], [311.5, 549.3, 27.3, 0.2, 19.2, -96.5, 10], [311.5, 550.3, 22.6, 0.2, 19.2, -96.5, 50]],
    "6": [[290.8, 551.2, 22.7, 1.2, 18.6, -93.6, 50], [290.8, 551.2, 27.7, 1.1, 19.6, -93.6, 10], [290.8, 551.2, 22.7, 1.2, 18.6, -93.6, 50]],
    "7": [[330.9, 541.1, 20.1, 0.1, 20.2, -96.5, 50], [330.9, 540.1, 23.6, 0.1, 20.2, -96.5, 10], [330.9, 541.1, 20.1, 0.1, 20.2, -96.5, 50]],
    "8": [[310, 543, 19.6, 0.1, 20.2, -94.5, 50], [310, 543, 24.6, 0.1, 20.2, -94.5, 10], [310, 543, 19.6, 0.1, 20.2, -94.5, 50]],
    "9": [[289.3, 544.5, 20.1, 0.1, 20.2, -94.5, 50], [289.3, 543.5, 24.6, 0.1, 20.2, -94.5, 10], [289.3, 544.5, 20.1, 0.1, 20.2, -94.5, 50]],
    "0": [[309.5, 532.9, 16.6, 0.1, 20.2, -94.5, 50], [309.5, 532.9, 20.6, 0.1, 20.2, -94.5, 10], [309.5, 532.9, 16.6, 0.1, 20.2, -94.5, 50]],
    "backspace": [[310, 523.2, 12.6, 0.1, 20.2, -94.5, 50], [310, 523.2, 17.6, 0.1, 20.2, -94.5, 10], [310, 523.2, 12.6, 0.1, 20.2, -94.5, 50]],
    "cancel": [[329.3, 522.7, 12.6, 0.1, 20.2, -94.5, 50], [329.3, 520.7, 16.6, 0.1, 20.2, -94.5, 10], [329.3, 522.7, 12.6, 0.1, 20.2, -94.5, 50]],
    "ok": [[287.9, 524.7, 13.1, 0.1, 20.2, -94.5, 50], [287.9, 523.7, 17.6, 0.1, 20.2, -94.5, 10], [287.9, 524.7, 13.1, 0.1, 20.2, -94.5, 50]]
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
