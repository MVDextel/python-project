# Vairāku kameru kustības detektors (PyQt6 + OpenCV)

Šī Python darbvirsmas lietojumprogramma ļauj pieslēgt līdz pat 4 USB kamerām vienlaicīgi, attēlot to video plūsmas un automātiski ierakstīt video failus, kad tiek konstatēta kustība. Tā ir piemērota video novērošanai, drošības vajadzībām vai vienkāršai uzraudzībai.

## Funkcijas

- Atbalsta līdz 4 USB kamerām vienlaicīgi
- Kustības detektēšana, izmantojot `cv2.createBackgroundSubtractorMOG2`
- Automātiska video ierakstīšana kustības gadījumā
- Notikumu žurnālu izveide ar laika zīmēm (`motion_log.txt`)
- Laika un kameras nosaukuma attēlošana uz video plūsmas
- Automātiska kameru pievienošana un noņemšana reāllaikā

## Tehnoloģijas

- Python 3.10+
- PyQt6
- OpenCV
- PyGrabber (DirectShow kameru saraksta iegūšanai)
- NumPy
- PyInstaller (lai izveidotu .exe versiju)

## Datu saglabāšana

Visi ierakstītie video faili un žurnāli tiek saglabāti mapē `motion_clips/`, kas tiek automātiski izveidota programmas direktorijā.

Struktūra piemēram:

motion_clips/
  motion_2025-05-22_14-30-55.avi
  motion_log.txt

## Instalēšana

Nepieciešams Python 3.10 vai jaunāks. Lai instalētu atkarības:
- pip install pyqt6 opencv-python numpy pygrabber

Programmas palaišana:
- python main.py

.exe faila izveide ar PyInstaller
Lai izveidotu izpildāmo failu Windows sistēmām:
- pyinstaller --onefile --noconsole main.py


#Resursi un dokumentācija
- https://doc.qt.io/qtforpython-6/
- https://docs.python.org/3/
- https://opencv.org/
- https://realpython.com/python-logging/
- https://pypi.org/project/pygrabber/
- https://stackoverflow.com/questions/tagged/python
