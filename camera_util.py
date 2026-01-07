"""
camera_util.py
Utility functions for camera operations, capture, status, and streaming.
"""

import os
import uuid
import cv2
import numpy as np
from google.cloud import vision
from dotenv import load_dotenv
from flask import jsonify, send_file, Response
from config import SYSTEMS, CAPTURE_DIR


def open_camera(system_number=None):
    """
    Open camera based on system_number from SYSTEMS config.
    Defaults to webcam index 0 if not found.
    """
    try:
        camera_path = SYSTEMS[system_number]["devices"].get("camera", 0) if system_number else 0
        cam = cv2.VideoCapture(camera_path)
        if not cam.isOpened():
            return None
        return cam
    except Exception:
        return None


def undistort_fisheye(img, strength=0.00001):
    """
    Apply fisheye correction (barrel distortion correction).
    """
    h, w = img.shape[:2]
    distCoeff = np.zeros((4, 1), np.float64)
    distCoeff[0, 0] = -strength  # k1 (negative → barrel correction)
    cam = np.eye(3, dtype=np.float32)
    cam[0, 2] = w / 2.0  # center x
    cam[1, 2] = h / 2.0  # center y
    cam[0, 0] = w        # focal length x
    cam[1, 1] = w        # focal length y
    return cv2.undistort(img, cam, distCoeff)


def capture_receipt_handler(system_number):
    """
    Capture a receipt image from camera, correct distortion, save, and return file path.
    Creates a separate folder for each system inside CAPTURE_DIR.
    """
    if not system_number or system_number not in SYSTEMS:
        return jsonify({"status": "error", "message": "Invalid or missing system_number"}), 400

    cam = open_camera(system_number)
    if cam is None:
        return jsonify({"status": "error", "message": f"Camera not accessible for system {system_number}"}), 500

    # Warm-up frames (discard first few to allow camera to adjust)
    for _ in range(5):
        cam.read()

    ret, frame = cam.read()
    cam.release()

    if not ret:
        return jsonify({"status": "error", "message": "Failed to capture image"}), 500

    # Rotate + fisheye correction
    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    frame = undistort_fisheye(frame, strength=0.0005)

    # Ensure system-specific folder exists
    system_dir = os.path.join(CAPTURE_DIR, f"system_{system_number}")
    os.makedirs(system_dir, exist_ok=True)

    # Save image in that folder
    filename = os.path.join(system_dir, f"receipt_{uuid.uuid4().hex}.jpg")
    cv2.imwrite(filename, frame)

    return send_file(filename, mimetype="image/jpeg")


def camera_status_handler(system_number):
    """
    Check if the camera is accessible.
    """
    if not system_number or system_number not in SYSTEMS:
        return jsonify({"status": "error", "message": "Invalid or missing system_number"}), 400

    cam = open_camera(system_number)
    if cam:
        cam.release()
        return jsonify({"status": "success", "message": f"Camera is ON for system {system_number}"})
    else:
        return jsonify({"status": "error", "message": f"Camera not accessible for system {system_number}"}), 500


def gen_frames():
    """
    Generator that streams frames from default camera.
    """
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
def ocr(frame):
    """
    Perform OCR on an image (numpy array) using Google Vision API.
    Returns the extracted text as string.
    """
    try:
        # Load .env file (you can place it in project root)
        load_dotenv()  # reads .env automatically in current dir
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

        client = vision.ImageAnnotatorClient()

        # Convert OpenCV BGR to RGB
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Encode to bytes
        _, encoded_image = cv2.imencode('.jpg', rgb_image)
        content = encoded_image.tobytes()
        image = vision.Image(content=content)

        response = client.text_detection(image=image)
        texts = response.text_annotations
        if texts:
            return texts[0].description
        return ""
    except Exception as e:
        return f"Error in OCR: {e}"

def capture_and_ocr_handler(system_number):
    """
    Capture image in front of camera, apply optional correction, and return OCR text.
    """
    if not system_number or system_number not in SYSTEMS:
        return {"status": "error", "message": "Invalid or missing system_number"}

    cam = open_camera(system_number)
    if cam is None:
        return {"status": "error", "message": f"Camera not accessible for system {system_number}"}

    # Warm-up frames
    for _ in range(5):
        cam.read()

    ret, frame = cam.read()
    cam.release()

    if not ret:
        return {"status": "error", "message": "Failed to capture image"}

    # Rotate + optional fisheye correction
    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    frame = undistort_fisheye(frame, strength=0.0005)

    # Run OCR directly
    ocr_text = ocr(frame)

    return {"status": "success", "system_number": system_number, "ocr_text": ocr_text}