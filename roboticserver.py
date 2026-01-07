from flask import Flask, request, jsonify
import json
import time
import logging
from xarm.wrapper import XArmAPI

# === Config ===
XARM_IP = "192.168.1.159"
RECORDED_ACTION_FILE = "RECORDED_ACTIONS.json"
PIN_STEP_FILE = "PIN_STEPS.json"

# === Logger ===
logging.basicConfig(
    filename='robot_server.log',
    level=logging.INFO,
    format='%(asctime)s [API] %(message)s',
)

# === Init Robot ===
arm = XArmAPI(XARM_IP)
arm.connect()
arm.clean_error()
arm.clean_warn()
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(0)

# === Load Sequences ===
with open(RECORDED_ACTION_FILE, "r") as f:
    RECORDED = json.load(f)

with open(PIN_STEP_FILE, "r") as f:
    PIN_STEPS = json.load(f)

# === Flask App ===
app = Flask(__name__)

# === Aliases ===
button_alias = {
    "o": "ok", "O": "ok",
    "b": "backspace", "B": "backspace",
    "c": "cancel", "C": "cancel"
}

# === Helper: Execute Steps ===
def run_sequence(seq):
    for step in seq:
        step_type = step.get("type")
        
        if step_type == "move":
            arm.set_servo_angle(angle=step["joints"], speed=step["speed"], is_radian=False, wait=True)

        elif step_type == "sleep":
            time.sleep(step.get("duration", 0))

        elif step_type == "gripper_open":
            arm.open_lite6_gripper()
            time.sleep(step.get("delay", 0.5))  # Optional: wait after gripper open

        elif step_type == "gripper_close":
            arm.close_lite6_gripper()
            time.sleep(step.get("delay", 0.5))  # Optional: wait after gripper close

        else:
            logging.warning(f"Unknown step type: {step_type}")


# === PIN Entry ===
def run_pin_sequence(pin_str):
    run_sequence(PIN_STEPS["entry"])
    for ch in pin_str:
        key = button_alias.get(ch, ch)
        if key not in PIN_STEPS["buttons"]:
            return f"Invalid character: {ch}", False
        run_sequence(PIN_STEPS["buttons"][key])
    run_sequence(PIN_STEPS["exit"])
    return "PIN sequence completed", True

# === Unified Endpoint ===
@app.route("/payment_action", methods=["POST"])
def unified_action():
    data = request.json
    system = data.get("system")
    rack = data.get("rack")
    action = data.get("action", "").lower()
    pin = data.get("pin")

    if system is None or rack is None or not action:
        return jsonify({"status": "error", "message": "Missing system/rack/action"}), 400

    key = f"{action}_system{system}_rack{rack}"
    if key not in RECORDED:
        return jsonify({"status": "error", "message": f"No recorded action for '{key}'"}), 404

    try:
        logging.info(f"Executing action: {key}")
        run_sequence(RECORDED[key])
    except Exception as e:
        logging.exception("Action execution failed")
        return jsonify({"status": "error", "message": str(e)}), 500

    if pin:
        logging.info(f"Executing PIN sequence: {pin}")
        msg, ok = run_pin_sequence(pin)
        if not ok:
            return jsonify({"status": "error", "message": msg}), 400

    return jsonify({"status": "success", "message": f"Action '{key}' executed", "pin_executed": bool(pin)})

# === Health Check ===
@app.route("/healthcheck", methods=["GET"])
def health():
    return jsonify({"status": "xArm connected", "ip": XARM_IP})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
