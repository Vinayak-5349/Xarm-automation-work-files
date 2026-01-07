# Updated server by Vinayak - Multi-Arm Robotic Payment System
# Started on Aug 29, 2025

from flask import Flask, request, jsonify,Response
import time
from armsideclient import (
    SYSTEMS, task_queues, worker_threads, arm_connections, arm_status,
    last_call, last_call_lock, initialize_systems
)
import logging
import json
from barcode_utils import BarcodeGenerator, ImageConverter, SerialCommunication
from PIL import Image
from camera_util import (
    capture_receipt_handler,
    camera_status_handler,
    gen_frames,capture_and_ocr_handler
)
app = Flask(__name__)

@app.route("/payment_action", methods=["POST"])
def unified_action():
    """Unified endpoint for all robotic arm actions"""
    client_ip = request.remote_addr or "unknown"
     # Parse request
    now = time.time()
    data = request.get_json(silent=True) or {}
    system = data.get("system")
    rack = data.get("rack")
    action = (data.get("action") or "").lower().strip()
    pin = data.get("pin")
     # Validate system
    if system is None:
        return jsonify({"status": "error", "message": "System ID is required"}), 400
    if system not in SYSTEMS:
        return jsonify({"status": "error", "message": f"System {system} not found"}), 404
    # Rate limiting per IP per system (allows same IP to hit different arms simultaneously)
    rate_limit_key = f"{client_ip}_{system}"
    with last_call_lock:
        last_ts = last_call.get(rate_limit_key)
        if last_ts is not None and (now - last_ts) < 60:
            return jsonify({
                "status": "error",
                "message": "Please wait 1 minute before retrying the same system"
            }), 429
        last_call[rate_limit_key] = now
    # CASE 1: PIN ONLY (no action/rack specified)
    if not action and not rack and pin:
        meta = {"ip": client_ip, "action": "pin_only", "rack": None, "ts": now, "system": system}
        task_queues[system].put((None, pin, meta))# sequence=None, pin provided
        qsize = task_queues[system].qsize()
        logging.info(f"[System {system}] Queued PIN-only task {meta} | queue_size={qsize}")
        return jsonify({
            "status": "success",
            "message": f"PIN-only action queued for System {system}",
            "queue_size": qsize,
            "pin_executed": True,
            "system": system
        }), 200
    # CASE 2 & 3: Action-based tasks (with optional PIN)
    if not action or rack is None:
        return jsonify({"status": "error", "message": "Missing action or rack"}), 400

    system_cfg = SYSTEMS.get(system)
    actions = system_cfg.get("actions", {})
    if action not in actions:
        return jsonify({"status": "error", "message": f"Action '{action}' not available for system {system}"}), 404
    if rack not in actions[action]:
        return jsonify({"status": "error", "message": f"Rack {rack} not available for action '{action}' in system {system}"}), 404

    filepath = actions[action][rack]
    # Load sequence file
    try:
        if isinstance(filepath, str) and filepath.endswith(".json"):
            with open(filepath, "r") as f:
                sequence = json.load(f)
        else:
            sequence = filepath
    except Exception as e:
        logging.exception(f"Failed to load motion file: {filepath}")
        return jsonify({"status": "error", "message": f"Load failed: {e}"}), 500
    # Queue the task
    meta = {"ip": client_ip, "action": action, "rack": rack, "ts": now, "system": system}
    task_queues[system].put((sequence, pin, meta))
    qsize = task_queues[system].qsize()
    logging.info(f"[System {system}] Queued task {meta} | queue_size={qsize}")
    return jsonify({
        "status": "success",
        "message": f"Action '{action}' on system {system}, rack {rack} queued",
        "queue_size": qsize,
        "pin_executed": bool(pin),
        "system": system
    }), 200

@app.route("/system_status/<int:system_id>", methods=["GET"])
def get_system_status(system_id):
    if system_id not in SYSTEMS:
        return jsonify({"status": "error", "message": f"System {system_id} not found"}), 404
    try:
        arm_connected = system_id in arm_connections
        # Is the arm connected?
        arm_state = arm_status.get(system_id, "idle")
         # Arm state: idle or working
        queue_size = task_queues[system_id].qsize() if system_id in task_queues else 0
         # Tasks waiting in the queue
        status = {"system_id": system_id, "arm_connected": arm_connected, "arm_state": arm_state, "tasks_queued": queue_size}
        return jsonify({"status": "success", "data": status}), 200
    except Exception as e:
        logging.error(f"Error getting system {system_id} status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/healthcheck", methods=["GET"])
def health_check():
    try:
        system_id = request.args.get("system") # Get system ID from query params
        all_systems_status = {}
        if system_id: # If a system ID is provided
            try:
                system_id = int(system_id)
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid system ID"}), 400
            if system_id not in SYSTEMS:
                return jsonify({"status": "error", "message": f"System {system_id} not found"}), 404
            all_systems_status[system_id] = {
                "queue_size": task_queues[system_id].qsize() if system_id in task_queues else 0,
                "arm_connected": system_id in arm_connections,
                "worker_alive": worker_threads[system_id].is_alive() if system_id in worker_threads else False
            }
        else:# Return all systems if no system ID provided
            for sid in SYSTEMS.keys():
                all_systems_status[sid] = {
                    "tasks_queued": task_queues[sid].qsize() if sid in task_queues else 0,
                    "arm_connected": sid in arm_connections,
                    "arm_state": arm_status.get(sid, "idle")
                }
        return jsonify({"status": "success", "message": "Server is healthy", "systems": all_systems_status}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/ocr", methods=["GET"])
def capture_and_ocr():
    """
    Capture receipt image from camera and perform OCR.
    Returns OCR result as JSON.
    """
    system_number = request.args.get("system_number", type=int)
    if system_number is None:
        return jsonify({"status": "error", "message": "Missing system_number"}), 400

    # Call the single utility function in camera_util
    result = capture_and_ocr_handler(system_number)

    return jsonify(result)
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

        # Generate barcode
        barcode_generator = BarcodeGenerator(barcode_type="code128", data=sku)
        image = barcode_generator.generate()

        # Center it inside 128x128
        centered_img = Image.new('1', (128, 128), 1)
        offset_x = (128 - image.width) // 2
        offset_y = (128 - image.height) // 2
        centered_img.paste(image, (offset_x, offset_y))

        byte_data = ImageConverter.image_to_bytearray(centered_img)

        # Select barcode display port from SYSTEMS config
        port = SYSTEMS[system_number]["devices"]["barcode_display"]
        SerialCommunication.send_to_serial(byte_data, port=port)

        # Optional future extension: pick an action (tap/insert/swipe) automatically
        # Example: action_file = SYSTEMS[system_number]["actions"].get("insert", {}).get(1)
        # if action_file: run_action(action_file)

        return jsonify({
            "status": "success",
            "message": f"Barcode sent to system {system_number}",
            "port": port
        })

    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@app.route("/capture_receipt", methods=["GET"])
def capture_receipt():
    system_number = request.args.get("system_number", type=int)
    return capture_receipt_handler(system_number)


@app.route("/camera_status", methods=["GET"])
def camera_status():
    system_number = request.args.get("system_number", type=int)
    return camera_status_handler(system_number)


@app.route("/camera_preview", methods=["GET"])
def camera_preview():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    initialize_systems()
    logging.info("All systems initialized, starting Flask server")
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)
