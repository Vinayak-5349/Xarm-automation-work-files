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
xarm_ip = "192.168.1.159"
arm = XArmAPI(xarm_ip)
arm.connect()
arm.clean_error()
arm.clean_warn()
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(0)

RECORD_FILE = "swipe_system2_rack1(4a).json"
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
def normalize_angle(angle):
    # Wrap into [-180, 180]
    while angle > 180:
        angle -= 360
    while angle < -180:
        angle += 360
    return angle


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
        (2, 355),      # J3
        (-355, 355),   # J4
        (-119, 119),   # J5
        (-355, 355),   # J6
    ]

    for i, angle in enumerate(joint_angles):
        angle = normalize_angle(angle)  # normalize first
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
def move_to_cartesian2(cartesian_position, speed=20, wait=True, comment=None):
    """
    Move robot in a straight Cartesian line (using set_position),
    while recording the move into the JSON log.
    
    cartesian_position: [x, y, z, roll, pitch, yaw] in mm/deg
    """
    if comment:
        print(f"--- {comment} ---")

    x, y, z, roll, pitch, yaw = cartesian_position

    # Send linear move
    def _do_move():
        return arm.set_position(
            x=x, y=y, z=z,
            roll=roll, pitch=pitch, yaw=yaw,
            speed=speed,
            wait=wait, is_radian=False, relative=False
        )

    # Record in JSON (same format as move_to_cartesian)
    timed_call(
        "linear_move",
        {
            "cartesian": cartesian_position,
            "speed": speed
        },
        _do_move
    )

    print("[OK] Linear move successful")
    return True

def rotate_joint(joint_index, delta_deg, speed=20, wait=True):
    _, current_angles = arm.get_servo_angle(is_radian=False)
    if not current_angles:
        print("[ERROR] Failed to read current joint angles")
        return False

    new_angles = current_angles[:]
    idx = joint_index - 1
    new_angles[idx] += delta_deg

    def _do_move():
        return arm.set_servo_angle(angle=new_angles, speed=speed, is_radian=False, wait=wait)

    # Record this as a "move" with updated joints
    timed_call(
        "move",
        {
            "joints": new_angles,
            "speed": speed
        },
        _do_move
    )

    print(f"[OK] Rotated Joint {joint_index} by {delta_deg}° → New angle: {new_angles[idx]:.2f}°")
    return True
def move_tool_relative(dx=0, dy=0, dz=0, droll=0, dpitch=0, dyaw=0, speed=20, comment=None):
    """
    Move the robot along tool axes by given deltas.
    Records the move into JSON log as tool-relative, not joint angles.
    """
    if comment:
        print(f"--- {comment} ---")

    # Allow list/tuple input
    if isinstance(dx, (list, tuple)) and len(dx) == 6:
        dx, dy, dz, droll, dpitch, dyaw = dx

    # --- SAFETY CHECK ---
    # Ensure inputs are floats (SDK requires float, not int/str/list)
    try:
        dx, dy, dz, droll, dpitch, dyaw = map(float, [dx, dy, dz, droll, dpitch, dyaw])
    except Exception as e:
        logging.error(f"Invalid tool move inputs: {e}")
        return False

    # Send tool-relative move WITH RECORDING
    def _do_move():
        return arm.set_tool_position(
            x=dx, y=dy, z=dz,
            roll=droll, pitch=dpitch, yaw=dyaw,
            speed=speed, wait=True
        )

    # timed_call will measure delay + record step automatically
    timed_call(
        "tool_move",
        {"dx": dx, "dy": dy, "dz": dz, "droll": droll, "dpitch": dpitch, "dyaw": dyaw, "speed": speed},
        _do_move
    )

    print("[OK] Tool-relative move successful")
    return True
def move_along_tool_x(dx, speed=10):
    timed_call("tool_move", {"dx": dx, "dy": 0, "dz": 0, "speed": speed},
               arm.set_tool_position, dx, 0, 0, 0, 0, 0, speed=speed, wait=True)
def move_to_joints(target_angles, speed=20, wait=True):
    """
    Move robot to a specific set of joint angles (absolute),
    record the move step into JSON log.
    """
    # Ensure 6 joint values only
    if len(target_angles) != 6:
        print("[ERROR] Expected 6 joint angles, got", len(target_angles))
        return False

    # Convert to floats
    new_angles = [float(a) for a in target_angles]

    def _do_move():
        return arm.set_servo_angle(angle=new_angles, speed=speed, is_radian=False, wait=wait)

    # Record step in JSON
    timed_call(
        "move",
        {
            "joints": new_angles,
            "speed": speed
        },
        _do_move
    )

    print(f"[OK] Moved to joint angles: {new_angles}")
    return True


# === Wrapper for Gripper Open/Close ===S
def open_gripper():
    timed_call("gripper_open", {}, lambda: arm.open_lite6_gripper())

def close_gripper():
    timed_call("gripper_close", {}, lambda: arm.close_lite6_gripper())

# === INSERT SEQUENCE RECORDING ===
def swipe_rack1():
    logging.info("Started recording: SWIPE action, Rack 1")
    recorded_sequence["current"] = []


    #pick up start
    move_to_cartesian([59,608.9,-6.4,6.7,1,173.1],speed=95)  
    move_to_cartesian([1.5,611.2,54.7,21.6,0.4,175.6],speed=95)
    open_gripper()
    timed_sleep(0.5)

    
    move_to_cartesian([4,653.9,162.7,21.6,0.4,175.6],speed=85)
    close_gripper()
    timed_sleep(0.5)
   
    move_to_cartesian([4,642.5,50.6,16.6,0.4,175.6],speed=95)
    
   
    move_to_cartesian([93.7,659.9,-42.5,89.9,-20.7,86.8],speed=95)
    # move_to_cartesian([93.7,659.9,-42.5,-87.8,20.8,-91],speed=95)
    
    move_to_cartesian([81.9,598.3,133,89.9,-20.7,86.8],speed=60)
    move_to_cartesian([81.3,596.3,140.3,89.9,-20.7,86.8],speed=60)
    move_to_cartesian([103.4,595.1,140.3,89.9,-20.7,86.8],speed=50)
    
    move_along_tool_x(-120,speed=90)
    move_to_cartesian([75.5,493.6,101,89.9,-20.7,86.8],speed=95)
    move_to_cartesian([87.5,641.7,-33.9,89.9,-20.7,86.8],speed=95)
    move_to_cartesian([59,608.9,-6.4,6.7,1,173.1],speed=95)  
    move_to_cartesian([1.5,611.2,54.7,21.6,0.4,175.6],speed=95)
    move_to_cartesian([4,653.9,162.7,21.6,0.4,175.6],speed=85)
    open_gripper()
    timed_sleep(0.5)
    move_to_cartesian([1.5,611.2,54.7,21.6,0.4,175.6],speed=95)
    close_gripper()
    move_to_cartesian([59,608.9,-6.4,6.7,1,173.1],speed=95) 

     
    return recorded_sequence["current"]  # return the steps

# === MAIN EXECUTION ===
def main():
    recorded_sequence["current"] = []  
    step_data = {}
    step_data["swipe_system1_rack1"] = swipe_rack1()

    with open(RECORD_FILE, "w") as f:
        json.dump(step_data, f, indent=4)

    logging.info(f"Saved all recorded steps to {RECORD_FILE}")

if __name__ == "__main__":
    main()
