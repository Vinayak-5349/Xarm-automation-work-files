# Updated server by Vinayak - Multi-Arm Robotic Payment System
# Started on Aug 29, 2025

import threading
import queue
from flask import Flask, request, jsonify, send_file, Response
import json
import time
import logging
import cv2
import os
import uuid
import numpy as np
from logging.handlers import RotatingFileHandler
from xarm.wrapper import XArmAPI
from config import SYSTEMS

# Logging setup
log_handler = RotatingFileHandler(
    'robot_server.log', maxBytes=500*1024, backupCount=3
)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s",
    handlers=[log_handler]
)

app = Flask(__name__)

# Global variables for threading and queue management
task_queues = {}           # {system_id: queue.Queue()}
worker_threads = {}        # {system_id: threading.Thread}
arm_connections = {}       # {system_id: XArmAPI}
last_call_lock = threading.Lock()
last_call = {}            # {ip: timestamp} for rate limiting

# Step handlers for different action types
def handle_move(arm, step):
    """Handle robotic arm movement"""
    try:
        arm.set_servo_angle(
            angle=step["joints"], 
            speed=step["speed"], 
            is_radian=False, 
            wait=True
        )
        if "delay" in step:
            time.sleep(step["delay"])
    except Exception as e:
        logging.error(f"Move failed: {e}")
        raise

def handle_sleep(arm, step):
    """Handle sleep/delay operations"""
    duration = step.get("duration", 0)
    time.sleep(duration)

def handle_open(arm, step):
    """Handle gripper open operation"""
    try:
        arm.open_lite6_gripper()
        time.sleep(step.get("delay", 0.5))
    except Exception as e:
        logging.error(f"Gripper open failed: {e}")
        raise

def handle_close(arm, step):
    """Handle gripper close operation"""
    try:
        arm.close_lite6_gripper()
        time.sleep(step.get("delay", 0.5))
    except Exception as e:
        logging.error(f"Gripper close failed: {e}")
        raise

STEP_HANDLERS = {
    "move": handle_move,
    "sleep": handle_sleep,
    "gripper_open": handle_open,
    "gripper_close": handle_close,
}

def run_sequence(arm, seq):
    """Execute a sequence of steps on the robotic arm"""
    if not seq:
        logging.warning("Empty sequence provided")
        return
        
    for i, step in enumerate(seq):
        try:
            stype = step.get("type")
            handler = STEP_HANDLERS.get(stype)
            if handler:
                logging.debug(f"Executing step {i+1}/{len(seq)}: {stype}")
                handler(arm, step)
            else:
                logging.warning(f"Unknown step type: {stype} in step {i+1}")
        except Exception as e:
            logging.error(f"Step {i+1} failed: {e}")
            raise

def run_pin_sequence(arm, pin_str, system_id):
    """Execute PIN entry sequence for specific system"""
    try:
        # Get PIN file path from system config
        system_cfg = SYSTEMS.get(system_id)
        if not system_cfg:
            raise ValueError(f"System {system_id} not found")
            
        pin_file = system_cfg["devices"].get("pin_entry")
        if not pin_file:
            raise ValueError(f"No PIN entry file configured for system {system_id}")
            
        # Load PIN steps from system-specific file
        with open(pin_file, "r") as f:
            pin_steps = json.load(f)

        logging.info(f"Starting PIN sequence for system {system_id}: {pin_str}")

        # Step 1: Move to entry position (system-specific)
        logging.debug("Executing entry sequence")
        run_sequence(arm, pin_steps["entry"])

        # Step 2: Press each PIN digit
        for i, ch in enumerate(pin_str):
            if ch not in pin_steps["buttons"]:
                raise ValueError(f"Invalid character: {ch}")
            
            logging.debug(f"Pressing button: {ch} ({i+1}/{len(pin_str)})")
            run_sequence(arm, pin_steps["buttons"][ch])

        # Step 3: Exit sequence (system-specific)
        logging.debug("Executing exit sequence")
        run_sequence(arm, pin_steps["exit"])
        
        logging.info(f"PIN sequence completed successfully for system {system_id}")
        return "PIN sequence completed", True
        
    except Exception as e:
        logging.error(f"PIN sequence failed for system {system_id}: {e}")
        return f"PIN sequence failed: {e}", False

def initialize_arm_connection(system_id):
    """Initialize connection to robotic arm for specific system"""
    try:
        system_cfg = SYSTEMS.get(system_id)
        if not system_cfg:
            raise ValueError(f"System {system_id} not found in config")
            
        arm_ip = system_cfg["arm_ip"]
        logging.info(f"Connecting to System {system_id} arm at {arm_ip}")
        
        arm = XArmAPI(arm_ip)
        arm.motion_enable(enable=True)
        arm.set_mode(0)
        arm.set_state(state=0)
        return arm
        
    except Exception as e:
        logging.error(f"Failed to connect to System {system_id} arm: {e}")
        raise

def worker_thread(system_id):
    """Worker thread for processing tasks for a specific robotic arm system"""
    logging.info(f"Worker thread started for System {system_id}")
    
    # Initialize arm connection
    try:
        arm = initialize_arm_connection(system_id)
        arm_status[system_id] = "idle"
    except Exception as e:
        logging.error(f"System {system_id} worker thread failed to start: {e}")
        return
    
    queue_obj = task_queues[system_id]
    
    while True:
        try:
            # Wait for task from queue
            sequence, pin, meta = queue_obj.get(timeout=None)
            
            if sequence is None and pin is None:
                # Shutdown signal
                logging.info(f"System {system_id} worker thread shutting down")
                break
            arm_status[system_id] = "working"  
            logging.info(f"System {system_id} processing task: {meta}")
            
            # Execute main sequence if provided
            if sequence:
                logging.info(f"Executing {meta['action']} sequence for rack {meta['rack']}")
                run_sequence(arm, sequence)
                
            # Execute PIN sequence if provided
            if pin:
                logging.info(f"Executing PIN sequence: {pin}")
                msg, success = run_pin_sequence(arm, pin, system_id)
                if not success:
                    logging.error(f"PIN sequence failed: {msg}")
                else:
                    logging.info("PIN sequence completed successfully")
                    
            logging.info(f"System {system_id} task completed successfully")
            arm_status[system_id] = "idle"
            try:
                arm.stop_lite6_gripper(sync=True)
                logging.info(f"Gripper stopped for system {system_id} after task completion")
            except Exception as e:
                 logging.error(f"Failed to stop gripper for system {system_id}: {e}")
        except queue.Empty:
            continue
        except Exception as e:
            logging.error(f"System {system_id} worker error: {e}")
        finally:
            queue_obj.task_done()

def initialize_systems():
    """Initialize task queues and worker threads for all systems"""
    for system_id in SYSTEMS.keys():
        # Create task queue for this system
        task_queues[system_id] = queue.Queue()
        
        # Start worker thread for this system
        thread = threading.Thread(
            target=worker_thread, 
            args=(system_id,), 
            daemon=True,
            name=f"System-{system_id}-Worker"
        )
        thread.start()
        worker_threads[system_id] = thread
        
        logging.info(f"System {system_id} initialized with worker thread")

@app.route("/payment_action", methods=["POST"])
def unified_action():
    """Unified endpoint for all robotic arm actions"""
    client_ip = request.remote_addr or "unknown"
    now = time.time()

    # Parse request
    data = request.get_json(silent=True) or {}
    system = data.get("system")
    rack = data.get("rack")
    action = (data.get("action") or "").lower().strip()
    pin = data.get("pin")

    # Validate system
    # Validate system
    if system is None:
        return jsonify({"status": "error", "message": "System ID is required"}), 400

    if system not in SYSTEMS:
        return jsonify({"status": "error", "message": f"System {system} not found"}), 404

    # Block insert actions if arm is busy (MUST BE BEFORE rate limit)
    if action in ("insert_up", "insert_down"):
        if arm_status.get(system) == "working":
            return jsonify({
                "status": "error",
                "message": "Insert action not allowed while arm is working"
            }), 409

    # Rate limiting
    rate_limit_key = f"{client_ip}_{system}"
    with last_call_lock:
        last_ts = last_call.get(rate_limit_key)
        if last_ts is not None and (now - last_ts) < 10:
            return jsonify({
                "status": "error",
                "message": "Please wait 10 sec before retrying the same system"
            }), 429
        last_call[rate_limit_key] = now


    # CASE 1: PIN ONLY (no action/rack specified)
    if not action and not rack and pin:
        meta = {"ip": client_ip, "action": "pin_only", "rack": None, "ts": now, "system": system}
        task_queues[system].put((None, pin, meta))  # sequence=None, pin provided
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
        return jsonify({
            "status": "error",
            "message": f"Action '{action}' not available for system {system}"
        }), 404
        
    if rack not in actions[action]:
        return jsonify({
            "status": "error",
            "message": f"Rack {rack} not available for action '{action}' in system {system}"
        }), 404

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

# Global dictionary to track arm working state
arm_status = {}  # {system_id: "idle" / "working"}

@app.route("/system_status/<int:system_id>", methods=["GET"])
def get_system_status(system_id):
    """Get real status of a specific robotic arm system"""
    if system_id not in SYSTEMS:
        return jsonify({"status": "error", "message": f"System {system_id} not found"}), 404
        
    try:
        # Is the arm connected?
        arm_connected = system_id in arm_connections
        
        # Arm state: idle or working
        arm_state = arm_status.get(system_id, "idle")
        
        # Tasks waiting in the queue
        queue_size = task_queues[system_id].qsize() if system_id in task_queues else 0
        
        status = {
            "system_id": system_id,
            "arm_connected": arm_connected,
            "arm_state": arm_state,
            "tasks_queued": queue_size
        }
        
        return jsonify({"status": "success", "data": status}), 200
        
    except Exception as e:
        logging.error(f"Error getting system {system_id} status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/screen_flow", methods=["POST"])
def screen_flow():
    client_ip = request.remote_addr or "unknown"
    now = time.time()
    data = request.get_json(silent=True) or {}

    system = data.get("system")
    choice = (data.get("choice") or "").lower().strip()
    confirm = (data.get("confirm") or "").lower().strip()
    denomination = (data.get("denomination") or "").strip()
    exact_amount = data.get("exact_amount")
    pin = data.get("pin")

    # ---------- SYSTEM VALIDATION ----------
    if system is None:
        return jsonify({"status": "error", "message": "System ID required"}), 400
    if system not in SYSTEMS:
        return jsonify({"status": "error", "message": f"System {system} not found"}), 404

    # ---------- RATE LIMIT ----------
    rate_key = f"{client_ip}_{system}"
    with last_call_lock:
        if rate_key in last_call and (now - last_call[rate_key]) < 10:
            return jsonify({"status": "error", "message": "Wait 10 seconds"}), 429
        last_call[rate_key] = now

    # ---------- STEP 1: FOOD / CASH ----------
    if choice not in ["food", "cash"]:
        return jsonify({
            "status": "need_input",
            "message": "Choose: food or cash",
            "next": "choice"
        }), 200

    # ---------- FOOD ----------
    if choice == "food":
        if not pin:
            return jsonify({
                "status": "need_pin",
                "message": "Enter PIN",
                "next": "pin"
            }), 200

        task_queues[system].put((None, pin, {
            "choice": "food",
            "confirm": "yes"
        }))

        return jsonify({"status": "success", "message": "Processing food"}), 200

    # ---------- CASH ----------
    if not confirm:
        return jsonify({
            "status": "need_input",
            "message": "Confirm cash? yes / no",
            "next": "confirm"
        }), 200

    if confirm == "no":
        if not pin:
            return jsonify({
                "status": "need_pin",
                "message": "Enter PIN",
                "next": "pin"
            }), 200

        task_queues[system].put((None, pin, {
            "choice": "cash",
            "confirm": "no"
        }))

        return jsonify({"status": "success", "message": "Processing cash (no)"}), 200

    # ---------- CASH YES ----------
    if not denomination:
        return jsonify({
            "status": "need_input",
            "message": "Choose denomination or other",
            "next": "denomination"
        }), 200

    if denomination == "other":
        if exact_amount is None:
            return jsonify({
                "status": "need_input",
                "message": "Enter exact amount",
                "next": "exact_amount"
            }), 200

    if not pin:
        return jsonify({
            "status": "need_pin",
            "message": "Enter PIN",
            "next": "pin"
        }), 200

    task_queues[system].put((None, pin, {
        "choice": "cash",
        "confirm": "yes",
        "denomination": denomination,
        "exact_amount": exact_amount
    }))

    return jsonify({"status": "success", "message": "Processing cash"}), 200



@app.route("/healthcheck", methods=["GET"])
def health_check():
    """Health check endpoint, optionally for a specific system"""
    try:
        system_id = request.args.get("system")  # Get system ID from query params
        all_systems_status = {}

        if system_id:  # If a system ID is provided
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
        else:  # Return all systems if no system ID provided
            for sid in SYSTEMS.keys():
                    all_systems_status[sid] = {
                                        "tasks_queued": task_queues[sid].qsize() if sid in task_queues else 0,
                                        "arm_connected": sid in arm_connections,
                                        "arm_state": arm_status.get(sid, "idle")
                                            }

                

        return jsonify({
            "status": "success",
            "message": "Server is healthy",
            "systems": all_systems_status
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    
        initialize_systems()
        
        logging.info("All systems initialized, starting Flask server")
        app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)
        
    