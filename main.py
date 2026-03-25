import cv2
import mediapipe as mp
import pygame
import time
import numpy as np
import ctypes
import csv
from datetime import datetime
import os
from datetime import datetime


from eye_utils import eye_aspect_ratio
from mouth_utils import mouth_aspect_ratio

from ui.dashboard import draw_header, draw_status_panel, draw_waiting, draw_calibration
from ui.profile_ui import draw_profile_cards, handle_click
from face_module.session_manager import save_session_to_db
from face_module.database import init_db
from face_module.face_engine import get_face_embedding
from face_module.profile_manager import (
    find_matching_profile,
    save_profile,
    load_profiles,
    delete_profile,
    update_name
)

# ---------------- INIT ----------------
init_db()

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

pygame.mixer.init()
pygame.mixer.music.load("assets/alarm.wav")

cap = cv2.VideoCapture(0)
cv2.namedWindow("Driver Monitoring System", cv2.WINDOW_NORMAL)

fullscreen = False

# Screen size
user32 = ctypes.windll.user32
SCREEN_W = user32.GetSystemMetrics(0)
SCREEN_H = user32.GetSystemMetrics(1)

# -------- RESIZE --------
def resize_with_aspect_ratio(frame, screen_w, screen_h):
    h, w = frame.shape[:2]

    scale = min(screen_w / w, screen_h / h)

    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(frame, (new_w, new_h))

    canvas = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)

    x_offset = (screen_w - new_w) // 2
    y_offset = (screen_h - new_h) // 2

    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

    return canvas, scale, x_offset, y_offset

# Landmarks
LEFT_EYE = [33,160,158,133,153,144]
RIGHT_EYE = [362,385,387,263,373,380]
MOUTH = [78,81,13,311,308,402,14,178]

EAR_THRESHOLD = 0.25
MAR_THRESHOLD = 0.50

blink_counter = 0
yawn_counter = 0

DROWSY_FRAMES = 20
YAWN_FRAMES = 15

calibration_start = 0
CALIB_DURATION = 5

ear_values = []
mar_values = []

embedding = None
current_profile = None
face_img = None

editing_mode = False
edit_text = ""
edit_profile_id = None

action_done = False
action_timer = 0
mode = "IDLE"

# -------- UI STATE --------
scroll_offset = 0
cards = []
mouse_click = None

# -------- SESSION STATS --------
total_blinks = 0
total_yawns = 0
drowsy_count = 0

ear_history = []
mar_history = []

# -------- MESSAGE --------
ui_message = ""
message_timer = 0

def show_message(frame, text):
    cv2.putText(frame, text, (50, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)

# -------- MOUSE --------
def mouse_callback(event, x, y, flags, param):
    global mouse_click
    if event == cv2.EVENT_LBUTTONDOWN:
        mouse_click = (x, y)

cv2.setMouseCallback("Driver Monitoring System", mouse_callback)


def draw_save_ui(frame, w, h):

    # Title
    cv2.putText(frame, "Save this profile?",
                (w//2 - 180, h//2 - 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,255),
                2)

    # SAVE button
    save_rect = (w//2 - 150, h//2, w//2 - 20, h//2 + 60)
    cv2.rectangle(frame, (save_rect[0], save_rect[1]),
                  (save_rect[2], save_rect[3]), (0,255,0), 2)
    cv2.putText(frame, "SAVE",
                (save_rect[0] + 20, save_rect[1] + 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0,255,0),
                2)

    # SKIP button
    skip_rect = (w//2 + 20, h//2, w//2 + 150, h//2 + 60)
    cv2.rectangle(frame, (skip_rect[0], skip_rect[1]),
                  (skip_rect[2], skip_rect[3]), (0,0,255), 2)
    cv2.putText(frame, "SKIP",
                (skip_rect[0] + 20, skip_rect[1] + 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0,0,255),
                2)

    return save_rect, skip_rect

def export_session(summary, driver_name):

    # Base folder
    base_dir = "driver_db/sessions"

    # Create driver-specific folder
    driver_folder = os.path.join(base_dir, driver_name.replace(" ", "_"))

    os.makedirs(driver_folder, exist_ok=True)

    # File name with timestamp
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
    file_path = os.path.join(driver_folder, filename)

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["Metric", "Value"])
        writer.writerow(["Driver", driver_name])
        writer.writerow(["Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])
        writer.writerow(["Blinks", summary["blinks"]])
        writer.writerow(["Yawns", summary["yawns"]])
        writer.writerow(["Avg EAR", summary["ear"]])
        writer.writerow(["Avg MAR", summary["mar"]])
        writer.writerow(["Drowsy Count", summary["drowsy"]])

    return file_path

def draw_summary(frame, w, h, summary):

    x1, y1 = w//2 - 250, h//2 - 200
    x2, y2 = w//2 + 250, h//2 + 200

    # Background
    cv2.rectangle(frame, (x1,y1), (x2,y2), (30,30,30), -1)
    cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,255), 2)

    # Title
    cv2.putText(frame, "Session Summary",
                (x1+60, y1+40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                (0,255,255), 2)

    # Stats
    labels = [
        f"Blinks: {summary['blinks']}",
        f"Yawns: {summary['yawns']}",
        f"Avg EAR: {summary['ear']:.2f}",
        f"Avg MAR: {summary['mar']:.2f}",
        f"Drowsy Count: {summary['drowsy']}"
    ]

    for i, text in enumerate(labels):
        cv2.putText(frame, text,
                    (x1+40, y1+90 + i*30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255,255,255),
                    2)

    # -------- BUTTONS --------

    # EXPORT
    export_rect = (x1+20, y2-70, x1+140, y2-20)
    cv2.rectangle(frame,
                  (export_rect[0], export_rect[1]),
                  (export_rect[2], export_rect[3]),
                  (255,0,0), 2)
    cv2.putText(frame, "EXPORT",
                (export_rect[0]+10, export_rect[1]+35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255,0,0), 2)

    # SAVE
    save_rect = (x1+170, y2-70, x1+300, y2-20)
    cv2.rectangle(frame,
                  (save_rect[0], save_rect[1]),
                  (save_rect[2], save_rect[3]),
                  (0,255,0), 2)
    cv2.putText(frame, "SAVE",
                (save_rect[0]+25, save_rect[1]+35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0,255,0), 2)

    # CLOSE
    close_rect = (x1+330, y2-70, x1+460, y2-20)
    cv2.rectangle(frame,
                  (close_rect[0], close_rect[1]),
                  (close_rect[2], close_rect[3]),
                  (0,0,255), 2)
    cv2.putText(frame, "CLOSE",
                (close_rect[0]+20, close_rect[1]+35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0,0,255), 2)

    return export_rect, save_rect, close_rect
# ---------------- LOOP ----------------
try:
    while True:

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        h, w, _ = frame.shape
        status = "WAITING"

        draw_header(frame)

        if time.time() - message_timer < 3:
            show_message(frame, ui_message)

        # -------- IDLE --------
        if mode == "IDLE":
            draw_waiting(frame, w, h)

        # -------- SEARCH --------
        elif mode == "SEARCH":

            embedding = get_face_embedding(frame)

            if embedding is not None:

                profile = find_matching_profile(embedding)

                if profile:
                    current_profile = profile
                    EAR_THRESHOLD = profile["ear"]
                    MAR_THRESHOLD = profile["mar"]

                    ui_message = f"Welcome {profile['name']}"
                    message_timer = time.time()

                    mode = "RUN"

                else:
                    ui_message = "New driver detected"
                    message_timer = time.time()

                    mode = "CALIBRATE"
                    calibration_start = time.time()
                    ear_values.clear()
                    mar_values.clear()

        # -------- CALIBRATE --------
        elif mode == "CALIBRATE":
            face_img = frame.copy()

            if results.multi_face_landmarks:

                for face_landmarks in results.multi_face_landmarks:

                    left_eye, right_eye, mouth = [], [], []

                    for idx in LEFT_EYE:
                        left_eye.append((int(face_landmarks.landmark[idx].x * w),
                                         int(face_landmarks.landmark[idx].y * h)))

                    for idx in RIGHT_EYE:
                        right_eye.append((int(face_landmarks.landmark[idx].x * w),
                                          int(face_landmarks.landmark[idx].y * h)))

                    for idx in MOUTH:
                        mouth.append((int(face_landmarks.landmark[idx].x * w),
                                      int(face_landmarks.landmark[idx].y * h)))

                    ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0
                    mar = mouth_aspect_ratio(mouth)

                    ear_values.append(ear)
                    mar_values.append(mar)

                    elapsed = time.time() - calibration_start
                    progress = min(elapsed / CALIB_DURATION, 1.0)

                    draw_calibration(frame, w, h, int(CALIB_DURATION - elapsed), progress)

                    if elapsed >= CALIB_DURATION:
                        EAR_THRESHOLD = np.mean(ear_values) - 0.05
                        MAR_THRESHOLD = np.mean(mar_values) + 0.10
                        face_img = frame.copy()
                        mode = "ASK_SAVE"

        # -------- ASK SAVE --------
        elif mode == "ASK_SAVE":
            

            save_rect, skip_rect = draw_save_ui(frame, w, h)

            if mouse_click is not None:

                mx, my = mouse_click

                # Convert to original frame coords
                mx = int((mx - x_offset) / scale)
                my = int((my - y_offset) / scale)

                if 0 <= mx < w and 0 <= my < h:

                    # SAVE clicked
                    if (save_rect[0] < mx < save_rect[2]) and (save_rect[1] < my < save_rect[3]):
                        save_profile(embedding, EAR_THRESHOLD, MAR_THRESHOLD, face_img)

                        ui_message = "Profile saved!"
                        message_timer = time.time()

                        mode = "RUN"

                    # SKIP clicked
                    elif (skip_rect[0] < mx < skip_rect[2]) and (skip_rect[1] < my < skip_rect[3]):
                        mode = "RUN"

                mouse_click = None

        # -------- RUN --------
        elif mode == "RUN":

            status = "ALERT"

            if results.multi_face_landmarks:

                for face_landmarks in results.multi_face_landmarks:

                    left_eye, right_eye, mouth = [], [], []

                    for idx in LEFT_EYE:
                        left_eye.append((int(face_landmarks.landmark[idx].x * w),
                                         int(face_landmarks.landmark[idx].y * h)))

                    for idx in RIGHT_EYE:
                        right_eye.append((int(face_landmarks.landmark[idx].x * w),
                                          int(face_landmarks.landmark[idx].y * h)))

                    for idx in MOUTH:
                        mouth.append((int(face_landmarks.landmark[idx].x * w),
                                      int(face_landmarks.landmark[idx].y * h)))

                    ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0
                    mar = mouth_aspect_ratio(mouth)

                    ear_history.append(ear)
                    mar_history.append(mar)

                    if ear < EAR_THRESHOLD:
                        blink_counter += 1

                        if blink_counter == 1:
                            total_blinks += 1

                        if blink_counter >= DROWSY_FRAMES:
                            status = "DROWSY"
                            drowsy_count += 1
                    else:
                        blink_counter = 0
                    if mar > MAR_THRESHOLD:
                        yawn_counter += 1

                        if yawn_counter == 1:
                            total_yawns += 1
                        if yawn_counter >= YAWN_FRAMES:
                            status = "DROWSY"
                            drowsy_count += 1
                            yawn_counter = 0
                    else:
                        yawn_counter = 0

                    draw_status_panel(frame, ear, mar, status)
                    # -------- ALARM --------
                    if status == "DROWSY":
                        if not pygame.mixer.music.get_busy():
                            pygame.mixer.music.play(-1)  # loop
                    else:
                        pygame.mixer.music.stop()

        # -------- PROFILE UI --------
        elif mode == "PROFILE_VIEW":

            profiles = load_profiles()

            cv2.putText(frame, "Profile Manager (ESC to exit)",
                        (50, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0,255,255),
                        2)

            cards = draw_profile_cards(frame, profiles, scroll_offset, -1)

            if mouse_click is not None:

                mx, my = mouse_click

                # Fix scaling issue
                mx = int((mx - x_offset) / scale)
                my = int((my - y_offset) / scale)

                if 0 <= mx < w and 0 <= my < h:
                    action, idx = handle_click(mx, my, cards, profiles)
                else:
                    action, idx = None, None

                if action == "select":
                    current_profile = profiles[idx]
                    EAR_THRESHOLD = current_profile["ear"]
                    MAR_THRESHOLD = current_profile["mar"]
                    mode = "RUN"

                elif action == "delete":
                    delete_profile(profiles[idx]["id"])

                elif action == "edit":
                    editing_mode = True
                    edit_profile_id = profiles[idx]["id"]
                    edit_text = profiles[idx]["name"]

                mouse_click = None
        # -------- EDIT UI --------
        if editing_mode:

            box_w, box_h = 400, 120
            x1 = w//2 - box_w//2
            y1 = h//2 - box_h//2

            # Background
            cv2.rectangle(frame, (x1, y1), (x1+box_w, y1+box_h), (40,40,40), -1)
            cv2.rectangle(frame, (x1, y1), (x1+box_w, y1+box_h), (0,255,255), 2)

            # Title
            cv2.putText(frame, "Edit Name",
                        (x1+20, y1+30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0,255,255),
                        2)

            # Text input
            cv2.putText(frame, edit_text,
                        (x1+20, y1+80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255,255,255),
                        2)

            # Hint
            cv2.putText(frame, "Enter = Save | ESC = Cancel",
                        (x1+20, y1+105),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (200,200,200),
                        1)
        # -------- SUMMARY --------
        elif mode == "SUMMARY":

            avg_ear = np.mean(ear_history) if ear_history else 0
            avg_mar = np.mean(mar_history) if mar_history else 0

            summary = {
                "blinks": total_blinks,
                "yawns": total_yawns,
                "ear": avg_ear,
                "mar": avg_mar,
                "drowsy": drowsy_count
            }

            export_rect, save_rect, close_rect = draw_summary(frame, w, h, summary)

            if mouse_click is not None:

                mx, my = mouse_click  

                # Convert to original frame coords
                mx = int((mx - x_offset) / scale)
                my = int((my - y_offset) / scale)

                if export_rect[0] < mx < export_rect[2] and export_rect[1] < my < export_rect[3]:
                    driver_name = current_profile["name"] if current_profile else "Unknown"
                    file_path = export_session(summary, driver_name)
                    ui_message = "Exported successfully!"
                    message_timer = time.time()
                    action_done = True
                    action_timer = time.time()

                elif save_rect[0] < mx < save_rect[2] and save_rect[1] < my < save_rect[3]:
                    driver_name = current_profile["name"] if current_profile else "Unknown"
                    save_session_to_db(summary, driver_name)
                    ui_message = "Session saved!"
                    message_timer = time.time()
                    action_done = True
                    action_timer = time.time()

                elif close_rect[0] < mx < close_rect[2] and close_rect[1] < my < close_rect[3]:
                    break

                # -------- SUCCESS MESSAGE --------
                if action_done:

                    cv2.putText(frame, ui_message,
                                (w//2 - 120, h//2 + 180),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                (0,255,0),
                                2)

                    # Auto close after 2 seconds
                    if time.time() - action_timer > 4:
                        break

                mouse_click = None
        # -------- DISPLAY --------
        display_frame, scale, x_offset, y_offset = resize_with_aspect_ratio(
            frame, SCREEN_W, SCREEN_H
        )
        cv2.imshow("Driver Monitoring System", display_frame)

        key = cv2.waitKey(1) & 0xFF

        if editing_mode:

            if key == 13:  # ENTER
                update_name(edit_profile_id, edit_text)
                editing_mode = False

                ui_message = "Name updated!"
                message_timer = time.time()

            elif key == 27:  # ESC
                editing_mode = False

            elif key == 8:  # BACKSPACE
                edit_text = edit_text[:-1]

            elif 32 <= key <= 126:  # normal typing
                edit_text += chr(key)

            continue 
        
        if key == ord('c') and mode == "IDLE":
            mode = "SEARCH"

        if key == ord('p'):
            mode = "PROFILE_VIEW"

        if key == ord('w') and mode == "PROFILE_VIEW":
            scroll_offset -= 50

        if key == ord('s') and mode == "PROFILE_VIEW":
            scroll_offset += 50

        if key == 27:
            if mode == "PROFILE_VIEW":
                mode = "IDLE"
            else:
                mode = "SUMMARY"

except KeyboardInterrupt:
    print("Stopped")

finally:
    pygame.mixer.music.stop()
    cap.release()
    cv2.destroyAllWindows()