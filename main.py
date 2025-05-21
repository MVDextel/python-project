import sys
import os
import datetime  #текущее время
import cv2  # OpenCV
import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets  # GUI
from pygrabber.dshow_graph import FilterGraph  # Получение списка камер

MAX_CAMERAS = 4  # Максимальное количество камер
SINGLE_CAM_SIZE = (320, 240)  # Размер для отображения одной камеры

# НЕ ТРОГАТЬ
# Это необходимо для корректной работы как при запуске .py, так и .exe
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Папка для сохранения видео и логов
SAVE_DIR = os.path.join(BASE_DIR, 'motion_clips')
os.makedirs(SAVE_DIR, exist_ok=True)

fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Формат записи AVI
motion_delay = 60  # Количество кадров после движения до остановки записи, чтобы резкого обрыва не было

# Цвета для наложения текста
font_color = QtGui.QColor(255, 255, 0)  # Цвет текста (сейчас зеленый)
font_bg_color = QtGui.QColor(0, 0, 0, 160)  # Цвет фона текста (чёрный, прозрачный)

# Функция для логов
def write_log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)  # Лог в консоль
    with open(os.path.join(SAVE_DIR, 'motion_log.txt'), 'a', encoding='utf-8') as f:
        f.write(full_message + '\n')

# Список доступных камер
def get_available_cameras_pygrabber():
    devices = FilterGraph().get_input_devices()
    cams = {}
    for idx, name in enumerate(devices):
        cams[idx] = name
    return cams  # индекс -> имя камеры

# Класс камеры: QLabel + видеопоток + обработка движения
class CameraWidget(QtWidgets.QLabel):
    def __init__(self, index, device_name=None, parent=None):
        super().__init__(parent)
        self.index = index
        self.device_name = device_name or f"Cam{index+1}"
        self.cap = None
        self.available = False  # Изначально камера не доступна

        # Обнаружение движения с помощью BackgroundSubtractor
        self.motion_detector = cv2.createBackgroundSubtractorMOG2()
        self.frame_count = 0
        self.warmup_frames = 50  # Количество кадров до того, как будет начата проверка движения(чтобы не было ложных записей)
        self.motion_timer = 0  # Таймер задержки после окончания движения
        self.recording = False
        self.out = None 

        # QLabel настройка для отображения всего окна без отступов
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background-color: black;")

        self.open_camera()

        # Таймер для обновления кадра 
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30) # каждые ~30 мс

    # Подключаем камеру
    def open_camera(self):
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.index, cv2.CAP_MSMF)
        self.available = self.cap.isOpened()
        if self.available:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, SINGLE_CAM_SIZE[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, SINGLE_CAM_SIZE[1])
            write_log_event(f"Camera '{self.device_name}' connected.")
            self.frame_count = 0
        else:
            write_log_event(f"Camera '{self.device_name}' NOT available.")

    # Цикл обновления кадра
    def update_frame(self):
        if not self.available:
            self.clear()
            return

        ret, frame = self.cap.read()
        if not ret:
            self.available = False
            self.clear()
            write_log_event(f"Camera '{self.device_name}' disconnected or no frames.")
            self.cap.release()
            self.cap = None
            return

        frame = cv2.resize(frame, SINGLE_CAM_SIZE)
        self.frame_count += 1

        # Обнаружение движения
        if self.frame_count <= self.warmup_frames:
            self.motion_detector.apply(frame)
            motion_detected = False
        else:
            fgmask = self.motion_detector.apply(frame)
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            motion_detected = any(cv2.contourArea(c) > 500 for c in contours)

        if motion_detected:
            cv2.rectangle(frame, (0, 0), (SINGLE_CAM_SIZE[0] - 1, SINGLE_CAM_SIZE[1] - 1), (0, 0, 255), 2)
            self.motion_timer = motion_delay
            if not self.recording:
                self.start_recording()

        if self.motion_timer > 0:
            self.motion_timer -= 1
        elif self.recording:
            self.stop_recording()

        if self.recording and self.out is not None:
            self.out.write(frame)

        # Отображаем на QLabel
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QtGui.QImage(rgb_frame.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        self.setPixmap(pixmap.scaled(self.size(), QtCore.Qt.AspectRatioMode.IgnoreAspectRatio, QtCore.Qt.TransformationMode.FastTransformation))

    # Начало видео
    def start_recording(self):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = os.path.join(SAVE_DIR, f"motion_{timestamp}.avi")
        self.out = cv2.VideoWriter(filename, fourcc, 20.0, SINGLE_CAM_SIZE)
        self.recording = True
        write_log_event(f"[+] Camera '{self.device_name}' start recording: {filename}")

    # Остановка
    def stop_recording(self):
        write_log_event(f"[-] Camera '{self.device_name}' stop recording.")
        self.recording = False
        if self.out:
            self.out.release()
            self.out = None

    # Освобождаем ресурсы
    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None
        if self.out:
            self.out.release()
            self.out = None
        self.recording = False
        self.timer.stop()

    # Наложение текста на всю запись
    def paintEvent(self, event):
        if self.pixmap() is None:
            return
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        if not painter.isActive():
            return

        painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
        font = QtGui.QFont('Arial', 12, QtGui.QFont.Weight.Bold)
        painter.setFont(font)

        metrics = QtGui.QFontMetrics(font)
        total_cameras = len(self.parent().findChildren(CameraWidget)) if self.parent() else 1
        text = f"Cam{self.index + 1}" if total_cameras == 1 else self.device_name

        rect = metrics.boundingRect(text).adjusted(-4, -2, 4, 2)
        x = 2
        y = self.height() - 5
        painter.fillRect(x - 2, y - rect.height(), rect.width() + 4, rect.height() + 4, font_bg_color)
        painter.setPen(font_color)
        painter.drawText(x, y, text)

        if self.index == 0:
            time_text = datetime.datetime.now().strftime("%H:%M:%S")
            time_rect = metrics.boundingRect(time_text).adjusted(-4, -2, 4, 2)
            x_time = 2
            y_time = time_rect.height() + 2
            painter.fillRect(x_time - 2, 0, time_rect.width() + 4, time_rect.height() + 4, font_bg_color)
            painter.drawText(x_time, y_time, time_text)

        painter.end()

# Окно приложения
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python-project")
        self.setMinimumSize(SINGLE_CAM_SIZE[0] * 2, SINGLE_CAM_SIZE[1] * 2)

        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)

        self.grid = QtWidgets.QGridLayout(self.widget)
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)

        self.cameras = {}

        # Таймер на автоматическое обновление списка камер
        self.refresh_cameras_timer = QtCore.QTimer(self)
        self.refresh_cameras_timer.timeout.connect(self.refresh_cameras)
        self.refresh_cameras_timer.start(5000)  # Каждые 5 секунд

        self.refresh_cameras()

    # Подключение/отключение камер (как же я намучился с этой...)
    def refresh_cameras(self):
        available_cams = get_available_cameras_pygrabber()

        for idx in list(self.cameras.keys()):
            if idx not in available_cams:
                cam_widget = self.cameras.pop(idx)
                self.grid.removeWidget(cam_widget)
                cam_widget.release()
                cam_widget.deleteLater()

        for idx, name in available_cams.items():
            if idx not in self.cameras and len(self.cameras) < MAX_CAMERAS:
                cam_widget = CameraWidget(idx, device_name=name, parent=self.widget)
                self.cameras[idx] = cam_widget
                row = len(self.cameras) // 2
                col = len(self.cameras) % 2
                self.grid.addWidget(cam_widget, row, col)

    def closeEvent(self, event):
        for cam in self.cameras.values():
            cam.release()
        super().closeEvent(event)

# Запуск программы
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
