# Vairāku kameru kustības detektors (PyQt6 + OpenCV)

Šī Python darbvirsmas lietojumprogramma ļauj izveidot savienojumu ar vairākām USB kamerām, attēlot video plūsmas un automātiski saglabāt kustības konstatētos fragmentus.

## Funkcijas
- Atbalsta līdz 4 kamerām vienlaicīgi
- Kustības noteikšana (pamatojoties uz OpenCV)
- Automātiska video ierakstīšana kustības gadījumā
- Visu notikumu reģistrēšana `motion_log.txt`.
- Laika un kameras nosaukuma rādīšana
- Automātiska kameru savienošana/atvienošana

## Tehnoloģijas
- Python 3.10+
- PyQt6
- OpenCV
- PyGrabber (lai iegūtu DirectShow ierīču sarakstu)
- PyInstaller (lai izveidotu `.exe`)

## Datu saglabāšana
Visi faili (video un žurnāli) tiek saglabāti apakšmapē:


## Terminalā:
pip install pyqt6 opencv-python numpy pygrabber