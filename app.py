import cv2
import numpy as np
import datetime
import os
import math
import time

# Название окна, 
# название папки для сохранения видео,
# название лог файла,
# максимальное количество камер
WINDOW_NAME = 'Dynamic Multi-Camera Surveillance'
SAVE_DIR = 'motion_clips'
LOG_FILE = os.path.join(SAVE_DIR, 'motion_log.txt')
MAX_CAMERAS = 4

os.makedirs(SAVE_DIR, exist_ok=True)

fourcc = cv2.VideoWriter_fourcc(*'XVID')
single_cam_size = (320, 240)
motion_delay = 60

font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.5
font_color = (255, 255, 255)
font_thickness = 1

def write_log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open(LOG_FILE, 'a') as f:
        f.write(full_message + '\n')

# === Camera class ===
class CameraStream:
    def __init__(self, index):
        self.index = index
        self.capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        self.available_cam = self.capture.isOpened()
        self.motion_detector = cv2.createBackgroundSubtractorMOG2()
        self.frame_count = 0
        self.warmup_frames = 50

    def get_frame(self):
        if not self.available_cam or not self.capture.isOpened():
            self.available_cam = False
            return self._blank_frame("No Data"), False

        is_valid, frame = self.capture.read()
        if not is_valid:
            self.available_cam = False
            return self._blank_frame("No Data"), False

        frame = cv2.resize(frame, single_cam_size)
        self.frame_count += 1

        if self.frame_count <= self.warmup_frames:
            self.motion_detector.apply(frame)
            return frame, False

        fgmask = self.motion_detector.apply(frame)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        motion_detected = any(cv2.contourArea(cnt) > 500 for cnt in contours)

        if motion_detected:
            cv2.rectangle(frame, (0, 0), (single_cam_size[0] - 1, single_cam_size[1] - 1), (0, 0, 255), 2)

        cam_label = f"Cam {self.index}"
        cv2.putText(frame, cam_label, (5, single_cam_size[1] - 5), font, 0.5, (255, 255, 0), 1)
        return frame, motion_detected

    def _blank_frame(self, text):
        blank = np.zeros((single_cam_size[1], single_cam_size[0], 3), dtype=np.uint8)
        (w, h), _ = cv2.getTextSize(text, font, 1, 2)
        x = (single_cam_size[0] - w) // 2
        y = (single_cam_size[1] + h) // 2
        cv2.putText(blank, text, (x, y), font, 1, (255, 255, 255), 2)
        return blank

    def release(self):
        if self.capture and self.capture.isOpened():
            self.capture.release()

# Управление камерами
active_cams = {}
last_cam_check = 0

def add_camera(index):
    if index in active_cams:
        return
    stream = CameraStream(index)
    if stream.available_cam:
        write_log_event(f"Camera {index} connected.")
        active_cams[index] = stream
    else:
        stream.release()

def update_active_cams():
    global active_cams, last_cam_check

    current_time = time.time()
    if current_time - last_cam_check < 5:
        return

    to_remove = []
    for idx, stream in active_cams.items():
        ret, _ = stream.capture.read()
        if not stream.capture.isOpened() or not ret:
            write_log_event(f"Camera {idx} disconnected or no frames.")
            stream.release()
            to_remove.append(idx)
    for idx in to_remove:
        del active_cams[idx]

    for i in range(MAX_CAMERAS):
        if i not in active_cams:
            add_camera(i)

    last_cam_check = current_time


# Создать окно с камерами
cv2.namedWindow(WINDOW_NAME)
recording = False
out = None
motion_timer = 0

for i in range(MAX_CAMERAS):
    add_camera(i)

# Главный цикл
while True:
    try:
        if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
            break
    except cv2.error:
        break

    update_active_cams()

    frames = []
    motion_status = []

    for stream in active_cams.values():
        frame, motion = stream.get_frame()
        frames.append(frame)
        motion_status.append(motion)

    n = len(frames)
    if n == 0:
        blank = np.zeros((240, 320, 3), dtype=np.uint8)
        cv2.putText(blank, "No Cameras", (50, 130), font, 1, (255, 255, 255), 2)
        cv2.imshow(WINDOW_NAME, blank)
        if cv2.waitKey(30) & 0xFF == 27:
            break
        continue

    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    padded_frames = frames + [np.zeros_like(frames[0])] * (rows * cols - n)
    grid_rows = [np.hstack(padded_frames[i*cols:(i+1)*cols]) for i in range(rows)]
    grid_frame = np.vstack(grid_rows)

    # Для времени
    time_text_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(grid_frame, time_text_now, (10, 20), font, font_scale, font_color, font_thickness, cv2.LINE_AA)

    # Запись видео при движении
    if any(motion_status):
        if not recording:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = os.path.join(SAVE_DIR, f"motion_{timestamp}.avi")
            out = cv2.VideoWriter(filename, fourcc, 20.0, (grid_frame.shape[1], grid_frame.shape[0]))
            write_log_event(f"[+] Start recording: {filename}")
            recording = True
        motion_timer = motion_delay
    elif recording:
        motion_timer -= 1
        if motion_timer <= 0:
            write_log_event("[-] Stop recording.")
            recording = False
            if out:
                out.release()
                out = None

    if recording and out:
        out.write(grid_frame)

    cv2.imshow(WINDOW_NAME, grid_frame)

    if cv2.waitKey(30) & 0xFF == 27:
        break

# Освобождает все камеры
for stream in active_cams.values():
    stream.release()
if out:
    out.release()
cv2.destroyAllWindows()
