from flask import Flask, request, jsonify,send_file, Response
 
import json
 
import time
 
import logging
 
import cv2
 
import os
 
import uuid

import numpy as np

from logging.handlers import RotatingFileHandler

from xarm.wrapper import XArmAPI
from PIL import Image
import treepoem
import serial
from config import (
    SYSTEMS,
    RECORDED_ACTION_FILE,
    PIN_STEP_FILE,
    
)


# === Logger ===
 
log_handler = RotatingFileHandler(
 
    'robot_server.log', maxBytes=500*1024, backupCount=3  # 500 KB, keep 3 backups
 
)
 
logging.basicConfig(
 
    level=logging.INFO,
 
    format='%(asctime)s [API] %(message)s',
 
    handlers=[log_handler]
 
)


 
# === Init Robot ===
 
ARMS = {}
for sys_id, cfg in SYSTEMS.items():
    try:
        arm = XArmAPI(cfg["arm_ip"])
        arm.connect()
        arm.clean_error()
        arm.clean_warn()
        arm.motion_enable(enable=True)
        arm.set_mode(0)
        arm.set_state(0)
        ARMS[sys_id] = arm
        logging.info(f"System {sys_id} connected to arm at {cfg['arm_ip']}")
    except Exception as e:
        logging.error(f"Failed to connect to arm {sys_id} at {cfg['arm_ip']}: {e}")

# === Load Sequences ===
with open(RECORDED_ACTION_FILE, "r") as f:
    RECORDED = json.load(f)

with open(PIN_STEP_FILE, "r") as f:
    PIN_STEPS = json.load(f)
 
# === Load Sequences ===
 

 
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
 
# === Barcode Generator ===

class BarcodeGenerator:

    def __init__(self, barcode_type: str, data: str):

        self.barcode_type = barcode_type.lower()

        self.data = data
 
    def generate(self) -> Image.Image:

        if self.barcode_type == "code128":

            return self.generate_code128_barcode(self.data)

        elif self.barcode_type == "gs1-databar-stacked-omni":

            return self.generate_GS1_DataBar_StackedOmni(self.data)

        elif self.barcode_type == "upc-a":

            bits = self.generate_upca(self.data)

            return ImageConverter.bits_to_image(bits)

        elif self.barcode_type == "ean-8":

            bits = self.generate_ean8(self.data)

            return ImageConverter.bits_to_image(bits)

        else:

            raise ValueError(f"Unsupported barcode type: {self.barcode_type}")
 
    def generate_GS1_DataBar_StackedOmni(self, data: str) -> Image.Image:

        try:

            image = treepoem.generate_barcode(

                barcode_type="databarstackedomni",

                data=f"01{data}"

            )

            return image.convert("1")

        except Exception as e:

            raise ValueError(f"Barcode generation failed: {e}")
 
    def generate_ean8(self, ean: str) -> str:

        if len(ean) != 8 or not ean.isdigit():

            raise ValueError("EAN-8 must be an 8-digit number")
 
        L_CODES = {str(i): format(i, '07b') for i in range(10)}

        R_CODES = {str(i): format(9 - i, '07b') for i in range(10)}
 
        bits = "101"

        for digit in ean[:4]:

            bits += L_CODES[digit]

        bits += "01010"

        for digit in ean[4:]:

            bits += R_CODES[digit]

        bits += "101"

        return bits
 
    def generate_upca(self, upca: str) -> str:

        if len(upca) != 12 or not upca.isdigit():

            raise ValueError("UPC-A must be a 12-digit number")
 
        L_CODES = {str(i): format(i, '07b') for i in range(10)}

        R_CODES = {str(i): format(9 - i, '07b') for i in range(10)}
 
        bits = "101"

        for digit in upca[:6]:

            bits += L_CODES[digit]

        bits += "01010"

        for digit in upca[6:]:

            bits += R_CODES[digit]

        bits += "101"

        return bits
 
    def generate_code128_barcode(self, data: str, target_width=128, target_height=128) -> Image.Image:

        try:

            image = treepoem.generate_barcode(

                barcode_type="code128",

                data=data

            ).convert("1")

            image = image.resize((target_width, target_height), Image.LANCZOS)

            return image

        except Exception as e:

            raise ValueError(f"Code 128 barcode generation failed: {e}")
 
class ImageConverter:

    @staticmethod

    def bits_to_image(bits: str, scale: int = 1, bar_height: int = 80) -> Image.Image:

        img = Image.new('1', (len(bits) * scale, bar_height), 1)

        for i, bit in enumerate(bits):

            if bit == '1':

                for x in range(scale):

                    for y in range(bar_height):

                        img.putpixel((i * scale + x, y), 0)
 
        display_width, display_height = 128, 128

        final_img = Image.new('1', (display_width, display_height), 1)

        offset_x = (display_width - img.width) // 2

        offset_y = (display_height - bar_height) // 2

        final_img.paste(img, (offset_x, offset_y))

        return final_img
 
    @staticmethod

    def image_to_bytearray(image: Image.Image) -> bytearray:

        pixel_bytes = bytearray()

        for y in range(128):

            for byte in range(0, 128, 8):

                bits = 0

                for bit in range(8):

                    pixel = image.getpixel((byte + bit, y))

                    if pixel != 0:

                        bits |= (1 << (7 - bit))

                pixel_bytes.append(bits)

        return pixel_bytes
 
class SerialCommunication:

    @staticmethod

    def send_to_serial(byte_data: bytearray, port, baud=115200, timeout=2):

        hex_code = ','.join(f'0x{b:02X}' for b in byte_data)

        data = f"barcode_image = bytearray([{hex_code}])\n__DONE__\n"

        try:

            with serial.Serial(port, baud, timeout=timeout) as ser:

                ser.write(data.encode('ascii'))

                logging.info(f"Barcode data sent successfully to {port}")

        except Exception as e:

            raise RuntimeError(f"Serial error on {port}: {e}")
 


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
 
last_call = {}

@app.route("/payment_action", methods=["POST"])
 
def unified_action():
 
    client_ip = request.remote_addr
 
    current_time = time.time()

    # Enforce 1-minute gap for each IP
 
    if client_ip in last_call and (current_time - last_call[client_ip]) < 60:
 
        return jsonify({"status": "error", "message": "Please wait 1 minute before retrying"}), 429

    # Update last call time
 
    last_call[client_ip] = current_time

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
 
# === Barcode Endpoint ===

@app.route("/generate-barcode", methods=["POST"])

def generate_barcode():

    try:

        data = request.get_json()

        if not data or "SKU" not in data or "system_number" not in data:

            return jsonify({"status": "error", "message": "Missing SKU or system_number"}), 400

        system_number = data["system_number"]

        if system_number not in SYSTEMS:

            return jsonify({"status": "error", "message": "Invalid system number"}), 400

        sku = data["SKU"]

        barcode_generator = BarcodeGenerator(barcode_type="code128", data=sku)

        image = barcode_generator.generate()

        centered_img = Image.new('1', (128, 128), 1)

        offset_x = (128 - image.width) // 2

        offset_y = (128 - image.height) // 2

        centered_img.paste(image, (offset_x, offset_y))

        byte_data = ImageConverter.image_to_bytearray(centered_img)

        # Use the port from config.py

        port = SYSTEMS[system_number]["devices"]["barcode_display"]

        SerialCommunication.send_to_serial(byte_data, port=port)

        return jsonify({"status": "success", "message": f"Barcode sent to system {system_number}"})

    except ValueError as ve:

        return jsonify({"status": "error", "message": str(ve)}), 400

    except Exception as e:

        return jsonify({"status": "error", "message": str(e)}), 500
 
# === Health Check ===
 
@app.route("/healthcheck", methods=["GET"])
 
def health():
 
    return jsonify({"status": "xArm connected", "systems": {k: v._ip for k, v in ARMS.items()}})

 
def open_camera(system_number):
    try:
        camera_path = SYSTEMS[system_number]["devices"].get("camera", 0)  # default webcam index 0
        cam = cv2.VideoCapture(camera_path)
        if not cam.isOpened():
            return None
        return cam
    except Exception:
        return None

def undistort_fisheye(img, strength=0.00001):

    h, w = img.shape[:2]

    distCoeff = np.zeros((4,1), np.float64)

    # Approximate barrel distortion coefficients

    distCoeff[0,0] = -strength   # k1 (negative → barrel correction)

    distCoeff[1,0] = 0.0         # k2

    distCoeff[2,0] = 0.0         # p1

    distCoeff[3,0] = 0.0         # p2

    cam = np.eye(3, dtype=np.float32)

    cam[0,2] = w/2.0   # center x

    cam[1,2] = h/2.0   # center y

    cam[0,0] = w       # focal length x

    cam[1,1] = w       # focal length y

    return cv2.undistort(img, cam, distCoeff)

@app.route("/capture_receipt", methods=["GET"])
def capture_receipt():
    system_number = request.args.get("system_number", type=int)
    if not system_number or system_number not in SYSTEMS:
        return jsonify({"status": "error", "message": "Invalid or missing system_number"}), 400

    cam = open_camera(system_number)
    if cam is None:
        return jsonify({"status": "error", "message": f"Camera not accessible for system {system_number}"}), 500

    # Warm-up frames
    for _ in range(5):
        cam.read()

    ret, frame = cam.read()
    cam.release()

    if not ret:
        return jsonify({"status": "error", "message": "Failed to capture image"}), 500

    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    frame = undistort_fisheye(frame, strength=0.0005)

    filename = os.path.join(CAPTURE_DIR, f"receipt_system{system_number}_{uuid.uuid4().hex}.jpg")
    cv2.imwrite(filename, frame)

    return send_file(filename, mimetype="image/jpeg")

# === API: Camera status check ===
 
@app.route("/camera_status", methods=["GET"])
def camera_status():
    system_number = request.args.get("system_number", type=int)
    if not system_number or system_number not in SYSTEMS:
        return jsonify({"status": "error", "message": "Invalid or missing system_number"}), 400

    cam = open_camera(system_number)
    if cam:
        cam.release()
        return jsonify({"status": "success", "message": f"Camera is ON for system {system_number}"})
    else:
        return jsonify({"status": "error", "message": f"Camera not accessible for system {system_number}"}), 500
 
def gen_frames():
 
    cam = open_camera()
 
    if cam is None:
 
        return
 
    while True:
 
        success, frame = cam.read()
 
        if not success:
 
            break
 
        _, buffer = cv2.imencode('.jpg', frame)
 
        frame = buffer.tobytes()
 
        yield (b'--frame\r\n'
 
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
 
    cam.release()

@app.route("/camera_preview", methods=["GET"])
 
def camera_preview():
 
    return Response(gen_frames(),
 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

 
 
if __name__ == "__main__":
 
    app.run(host="0.0.0.0", port=8000)

 