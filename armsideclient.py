import threading
import queue
import json
import time
import logging
from logging.handlers import RotatingFileHandler
from xarm.wrapper import XArmAPI
from config import SYSTEMS

# Logging setup
log_handler = RotatingFileHandler(
    'robot_server.log', maxBytes=500*1024, backupCount=3
)
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    handler = RotatingFileHandler(
        'robot_server.log', maxBytes=500*1024, backupCount=3
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

# Global variables for threading and queue management
task_queues = {}           # {system_id: queue.Queue()}
worker_threads = {}        # {system_id: threading.Thread}
arm_connections = {}       # {system_id: XArmAPI}
last_call_lock = threading.Lock()
last_call = {}             # {ip: timestamp} for rate limiting
arm_status = {}            # {system_id: "idle" / "working"}

# Step handlers
def handle_tool_move(arm, step):
    """Handle tool-relative move operation"""
    try:
        dx = step.get("dx", 0)
        dy = step.get("dy", 0)
        dz = step.get("dz", 0)
        rx = step.get("rx", 0)   # roll
        ry = step.get("ry", 0)   # pitch
        rz = step.get("rz", 0)   # yaw
        speed = step.get("speed", 20)

        arm.set_tool_position(
            x=dx, y=dy, z=dz,
            roll=rx, pitch=ry, yaw=rz,
            speed=speed, wait=True
        )

        if "delay" in step:
            time.sleep(step["delay"])

    except Exception as e:
        logging.error(f"Tool move failed: {e}")
        raise


def handle_move(arm, step):
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
    "tool_move": handle_tool_move,   # ✅ NEW
}


def run_sequence(arm, seq):
    """Execute a sequence of steps on the robotic arm"""
    if not seq:
        logging.warning("Empty sequence provided")
        return
       # Unwrap dict format like {"tap_system2_rack1": [ ... ]}
    if isinstance(seq, dict) and len(seq) == 1:
        seq = list(seq.values())[0]  
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
        run_sequence(arm, pin_steps["entry"])
        # Step 2: Press each PIN digit
        for i, ch in enumerate(pin_str):
            if ch not in pin_steps["buttons"]:
                raise ValueError(f"Invalid character: {ch}")
            logging.debug(f"Pressing button: {ch} ({i+1}/{len(pin_str)})")
            # Step 3: Exit sequence (system-specific)
            run_sequence(arm, pin_steps["buttons"][ch])
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
def load_interaction_json(system_id):
    """
    Loads the interaction/button motion JSON for a system
    """
    path = SYSTEMS[system_id]["interaction_file"]
    with open(path, "r") as f:
        return json.load(f)

def worker_thread(system_id):
    """Worker thread for processing tasks for a specific robotic arm system"""
    logging.info(f"Worker thread started for System {system_id}")

    # Initialize arm connection
    try:
        arm = initialize_arm_connection(system_id)
        arm_connections[system_id] = arm
        with last_call_lock:
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
                logging.info(f"System {system_id} worker thread shutting down")
                break

            with last_call_lock:
                arm_status[system_id] = "working"

            logging.info(f"System {system_id} processing task: {meta}")

            # ------------------------------------------------------------------
            # NEW ADDITION: Build dynamic sequence for choice / cash / pin flow
            # ------------------------------------------------------------------
            if meta.get("choice"):
                interaction = load_interaction_json(system_id)

                sequence = []
                sequence += interaction.get("entry", [])

                choice = meta.get("choice")
                denomination = meta.get("denomination")
                exact_amount = meta.get("exact_amount")
                confirm = meta.get("confirm")

                # Choice button (food / cash)
                if choice in interaction.get("buttons", {}):
                    sequence += interaction["buttons"][choice]

                # Cash logic
                if choice == "cash":
                    if denomination in {"0", "20", "30", "40", "50"}:
                        sequence += interaction["buttons"].get(denomination, [])
                    elif exact_amount is not None:
                        for d in str(exact_amount):
                            sequence += interaction["buttons"].get(d, [])

                # PIN digits
                if pin:
                    for d in str(pin):
                        sequence += interaction["buttons"].get(d, [])

                # Confirmation
                if confirm == "yes":
                    sequence += interaction["buttons"].get("yes", [])

            # ------------------------------------------------------------------
            # Existing execution logic (UNCHANGED)
            # ------------------------------------------------------------------
            if sequence:
                logging.info("Executing composed sequence")
                run_sequence(arm, sequence)

            # Old PIN-only flow (still works for legacy calls)
            if pin and not meta.get("choice"):
                logging.info(f"Executing PIN sequence: {pin}")
                msg, success = run_pin_sequence(arm, pin, system_id)
                if not success:
                    logging.error(f"PIN sequence failed: {msg}")
                else:
                    logging.info("PIN sequence completed successfully")

            logging.info(f"System {system_id} task completed successfully")

            with last_call_lock:
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
