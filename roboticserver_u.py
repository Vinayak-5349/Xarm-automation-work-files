from flask import Flask, request, jsonify
import json
import time
import logging
import serial
import threading
from PIL import Image
import treepoem
from pydantic import BaseModel
from xarm.wrapper import XArmAPI
from config import SYSTEMS, RECORDED_ACTION_FILE, PIN_STEP_FILE

# === Logger ===
logging.basicConfig(filename='robot_server.log', level=logging.INFO, format='%(asctime)s [API] %(message)s')

# === Init Arms ===
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

# === Flask App ===
app = Flask(__name__)

# === Aliases ===
button_alias = {"o": "ok", "O": "ok", "b": "backspace", "B": "backspace", "c": "cancel", "C": "cancel"}

# === Robot Control Helpers ===
def run_sequence(arm, seq):
    for step in seq:
        stype = step.get("type")
        if stype == "move":
            arm.set_servo_angle(angle=step["joints"], speed=step["speed"], is_radian=False, wait=True)
        elif stype == "sleep":
            time.sleep(step.get("duration", 0))
        elif stype == "gripper_open":
            arm.open_lite6_gripper()
            time.sleep(step.get("delay", 0.5))
        elif stype == "gripper_close":
            arm.close_lite6_gripper()
            time.sleep(step.get("delay", 0.5))

def validate_pin(pin):
    for ch in pin:
        key = button_alias.get(ch, ch)
        if key not in PIN_STEPS["buttons"]:
            return False, f"Invalid character in PIN: {ch}"
    return True, ""

def run_pin_sequence(arm, pin_str):
    run_sequence(arm, PIN_STEPS["entry"])
    for ch in pin_str:
        key = button_alias.get(ch, ch)
        run_sequence(arm, PIN_STEPS["buttons"][key])
    run_sequence(arm, PIN_STEPS["exit"])
    return "PIN sequence completed", True

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

# === Payment Action Endpoint ===
@app.route("/payment_action", methods=["POST"])
def payment_action():
    data = request.json
    system = data.get("system")
    rack = data.get("rack")
    action = data.get("action", "").lower()
    pin = data.get("pin")

    if system not in ARMS:
        return jsonify({"status": "error", "message": "Invalid system"}), 400

    key = f"{action}_system{system}_rack{rack}"
    if key not in RECORDED:
        return jsonify({"status": "error", "message": f"No recorded action for '{key}'"}), 404

    if pin:
        valid, msg = validate_pin(pin)
        if not valid:
            return jsonify({"status": "error", "message": msg}), 400

    def task():
        run_sequence(ARMS[system], RECORDED[key])
        if pin:
            run_pin_sequence(ARMS[system], pin)

    threading.Thread(target=task, daemon=True).start()
    return jsonify({"status": "success", "message": "Action started"})



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
    return jsonify({"status": "ok", "systems": list(SYSTEMS.keys())})

# === Arm Status Endpoint ===
@app.route("/arm-status", methods=["GET"])
def arm_status():
    data = request.get_json()
    system = data.get("system_number")

    if system not in ARMS:
        return jsonify({'status': 'error', 'message': 'Invalid system'}), 400
    
    arm = ARMS[system]
    try:
        state = arm.get_state()  # 1 = moving, 0 = idle
        is_busy = (state == 1)
        return jsonify({'system': system, 'busy': is_busy})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
