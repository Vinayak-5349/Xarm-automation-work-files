
import json
import time
import logging
from xarm.wrapper import XArmAPI

# === Setup Logger ===
logging.basicConfig(
    filename='robot_action.log',
    level=logging.INFO,
    format='%(asctime)s [API] %(message)s',
)

# === Connect to Robot ===
xarm_ip = "192.168.1.159"
arm = XArmAPI(xarm_ip)
arm.connect()   
arm.clean_error()
arm.clean_warn()
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(0)

# === Load recorded actions ===
# with open("Arm2trialtap.json", "r") as f:
#     RECORDED = json.load(f)

with open("tap_system2_rack1.json", "r") as f:
    RECORDED = json.load(f)

# === Request Schema ===

# === Play Recorded Steps ===
def run_sequence(seq):
    for step in seq:
        stype = step.get("type")

        if stype == "move":
            arm.set_servo_angle(
                angle=step["joints"],
                speed=step.get("speed", 20),
                is_radian=False,
                wait=True
            )

        elif stype == "tool_move":
            dx = step.get("dx", 0)
            dy = step.get("dy", 0)
            dz = step.get("dz", 0)
            rx = step.get("rx", 0)
            ry = step.get("ry", 0)
            rz = step.get("rz", 0)
            speed = step.get("speed", 20)

            arm.set_tool_position(
                x=dx, y=dy, z=dz,
                roll=rx, pitch=ry, yaw=rz,
                speed=speed, wait=True
            )

        elif stype == "sleep":
            time.sleep(step.get("duration", 0))

        elif stype == "gripper_open":
            arm.open_lite6_gripper()
            time.sleep(step.get("delay", 0.5))

        elif stype == "gripper_close":
            arm.close_lite6_gripper()
            time.sleep(step.get("delay", 0.5))


if __name__ == "__main__":
        # Only run when script is executed directly
        n=0
        while n<1:
            run_sequence(RECORDED["tap_system2_rack1"])
            n=n+1

# === API Endpoint ===

# async def play_action(request: ActionRequest):
#     key = f"{request.action.lower()}_system{request.system}_rack{request.rack}"
#     logging.info(f"Received request to play action: {key}")

#     if key not in RECORDED:
#         msg = f"Action '{key}' not found in recorded steps."
#         logging.error(msg)
#         return {"status": "error", "message": msg}

#     try:
#         play_sequence(RECORDED[key])
#         logging.info(f"Successfully executed action: {key}")
#         return {"status": "success", "message": f"Action '{key}' executed."}
#     except Exception as e:
#         logging.exception("Error during action execution")
#         return {"status": "error", "message": str(e)}
