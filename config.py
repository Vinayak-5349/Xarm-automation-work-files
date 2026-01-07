SYSTEMS = {
    1: {
        "arm_ip": "192.168.1.183",
        "devices": {
            "barcode_display": "/dev/ttyUSB3",
            "scanner": "/dev/ttyUSB4",
            "other_device": "/dev/ttyUSB5"
        },
        "actions": {
            # You can add tap/insert/swipe later if System 1 has them
        }
    },

    2: {
        "arm_ip": "192.168.1.159",
        "devices": {
            "barcode_display": "/dev/barcode_display",
            "scanner": "/dev/ttyUSB1",
            "other_device": "/dev/ttyUSB2",
            "camera": "/dev/ttyUSB2",
            "pin_entry": "Recorded_file/SYSTEM2/PIN.json"
        },
        "actions": {
            "tap": {
                1: "Recorded_file/SYSTEM2/TAP/Tap_system2_rack1.json",
                
            },
            "insert": {
                1: "Recorded_file/SYSTEM2/INSERT/Insert_system2_rack1.json"
            },
            "swipe": {
                1: "Recorded_file/SYSTEM2/INSERT/Insert_system2_rack1.json"
                
            }
        }
    },

    3: {
        "arm_ip": "192.168.1.189",
        "devices": {
            "barcode_display": "/dev/ttyUSB6",
            "scanner": "/dev/ttyUSB7",
            "other_device": "/dev/ttyUSB8"
        },
        "actions": {
            # Future actions for System 3 can be added here
        }
    }
}
#always save the recorded actions in same way as insert_system2_rack1,because the code is written to undersatnd in such a way.
CAPTURE_DIR = "captures"