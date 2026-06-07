import sys
import os
import traceback

# Custom excepthook to write stack trace
def my_excepthook(type, value, tb):
    with open("custom_crash.txt", "w") as f:
        traceback.print_exception(type, value, tb, file=f)
    print("CRASH CAPTURED!")
    sys.__excepthook__(type, value, tb)

sys.excepthook = my_excepthook

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fov_tools import MainWindow

app = QApplication(sys.argv)
win = MainWindow()

# Select first sensor
first_sensor_id = win._scene_cfg.sensors[0].id
win._signals.sensor_selected.emit(first_sensor_id)

# Modify coordinate repeatedly to see if we can trigger recursion or crash
print("Simulating multiple modifications...")
for i in range(10):
    win._prop_panel._x.setValue(1.0 + i * 0.1)

def check_after_redraw():
    print("No crash yet. Exiting.")
    app.quit()

QTimer.singleShot(2000, check_after_redraw)
app.exec_()
