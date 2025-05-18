import cv2
import numpy as np
import datetime
import os

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("Fail")
    exit()

fgbg = cv2.createBackgroundSubtractorMOG2()

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = None
recording = False
motion_timer = 0
motion_delay = 60

save_dir = 'motion_clips' #ПАПКА ДЛЯ ФАЙЛОВ, ОБЯЗАТЕЛЬНО СДЕЛАТЬ В ПРОЕКТЕ
os.makedirs(save_dir, exist_ok=True)

frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

window_name = 'Camera'
cv2.namedWindow(window_name)

warmup_frames = 50
frame_count = 0

font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.5
font_color = (255, 255, 255)
font_thickness = 1
text_position = (10, 20)

while True:
    try:
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            break
    except cv2.error:
        break

    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # display date and time on screen
    now_text = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, now_text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

    if frame_count <= warmup_frames:
        fgbg.apply(frame)
        cv2.imshow(window_name, frame)
        if cv2.waitKey(30) & 0xFF == 27:
            break
        continue

    fgmask = fgbg.apply(frame)
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    motion_detected = any(cv2.contourArea(cnt) > 500 for cnt in contours)

    if motion_detected:
        if not recording:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(save_dir, f"motion_{timestamp}.avi")
            out = cv2.VideoWriter(filename, fourcc, 20.0, (frame_width, frame_height))
            print(f"[+] Start recording: {filename}")
        recording = True
        motion_timer = motion_delay
    elif recording:
        motion_timer -= 1
        if motion_timer <= 0:
            print("[*] Stop recording.")
            recording = False
            out.release()
            out = None

    if recording and out:
        out.write(frame)

    cv2.imshow(window_name, frame)

    if cv2.waitKey(30) & 0xFF == 27:
        break

cap.release()
if out:
    out.release()
cv2.destroyAllWindows()
