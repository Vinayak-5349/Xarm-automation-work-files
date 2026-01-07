from flask import Flask, request, jsonify
import json
import time
from xarm.wrapper import XArmAPI

PIN_STEP_FILE = "PIN_STEPS.json"
xarm_ip = "192.168.1.159"
arm = XArmAPI(xarm_ip)
arm.connect()
arm.clean_error()
arm.clean_warn()
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(0)

# Load steps once on start
with open(PIN_STEP_FILE) as f:
    step_data = json.load(f)

# Mapping for convenience
button_alias = {
    "o": "ok", "O": "ok",
    "b": "backspace", "B": "backspace",
    "c": "cancel", "C": "cancel"
}

def run_step(step):
    if "type" not in step:
        print("[ERROR] Step missing 'type':", step)
        return

    if step["type"] == "move":
        if "joints" in step and "speed" in step:
            arm.set_servo_angle(angle=step["joints"], speed=step["speed"], is_radian=False, wait=True)
            time.sleep(0.05)
        else:
            print("[ERROR] Incomplete move step:", step)
    elif step["type"] == "sleep":
        if "duration" in step:
            time.sleep(step["duration"])
        else:
            print("[ERROR] Incomplete sleep step:", step)
    else:
        print(f"[ERROR] Unknown step type: {step['type']}")

def run_sequence(sequence):
    for i, step in enumerate(sequence):
        try:
            run_step(step)
        except Exception as e:
            print(f"[EXCEPTION] at step {i}: {step}")
            print(e)
def validate_steps(steps):
    for step in steps:
        if "type" not in step:
            raise ValueError("Missing 'type' in step")
        if step["type"] == "move" and ("joints" not in step or "speed" not in step):
            raise ValueError("Incomplete move step")
        if step["type"] == "sleep" and "duration" not in step:
            raise ValueError("Incomplete sleep step")

validate_steps(step_data["entry"])
validate_steps(step_data["exit"])
for key in step_data["buttons"]:
    validate_steps(step_data["buttons"][key])

def run_pin_sequence(pin_str):
    run_sequence(step_data["entry"])
    for ch in pin_str:
        key = button_alias.get(ch, ch)
        if key not in step_data["buttons"]:
            return f"Invalid character: {ch}", False
        run_sequence(step_data["buttons"][key])
    run_sequence(step_data["exit"])
    return "Success", True

app = Flask(__name__)

@app.route("/enter_pin", methods=["POST"])
def enter_pin():
    data = request.json
    pin = data.get("pin", "")
    if not pin:
        return jsonify({"status": "error", "message": "PIN not provided"}), 400

    print(f"[INFO] Executing PIN sequence: {pin}")
    message, ok = run_pin_sequence(pin)
    if ok:
        return jsonify({"status": "success", "message": f"PIN '{pin}' executed"})
    else:
        return jsonify({"status": "error", "message": message}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
