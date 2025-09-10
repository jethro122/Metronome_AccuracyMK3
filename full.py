
import playsound3
from playsound3 import playsound
import mido
import time
import threading
import statistics
import os
from PyQt6 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg

# --- SETTINGS ---
BPM = 120
INTERVAL = 60 / BPM
DEVICE_NAME = "Maschine"  # adjust if needed
CALIBRATION_OFFSET = -0.125  # seconds (~125 ms system latency)
ROLLING_WINDOW = 20
LOG_FILE = os.path.expanduser("~/practice_log.txt")

# --- GLOBALS ---
start_time = time.time()
beat_count = 0
errors = []
history = []



# --- SETTINGS ---
BPM = 120 # beats per minute
INTERVAL = 60 / BPM      # seconds per beat
DEVICE_NAME = 'Maschine Mikro MK3' # adjust if your MIDI port name differs
CALIBRATION_OFFSET = -0.115  # in seconds (negative if consistently late)
ROLLING_WINDOW = 20       # number of hits to average
LOG_FILE = "practice_log.txt"

# --- GLOBALS ---
start_time = time.time()
beat_count = 0
errors = []

def metronome():
    """Background metronome that prints ticks with expected times."""
    global beat_count
    sample_path = "/Users/jethrojoneslong/Downloads/sampleswap/5000_DRUMHITS/SAMPLES - 5000 DRUMHITS/THEMOSTP/BLOCK__2.wav"
    next_tick = start_time
    while True:
        # Wait until exact tick time
        now = time.time()
        sleep_time = next_tick - now
        if sleep_time > 0:
            time.sleep(sleep_time)

        print(f"[Tick {beat_count}] at {next_tick * 1000:.1f} ms")
        playsound(sample_path, block=False)
        beat_count += 1
        next_tick = start_time + beat_count * INTERVAL


def log_to_file(average_error):
    """Append average error to a text file with timestamp."""
    with open(LOG_FILE, "a") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp} - Average Error: {average_error:.1f} ms\n")

# --- GUI ---
class AccuracyApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pad Accuracy Tracker")
        self.setGeometry(200, 200, 600, 400)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        layout = QtWidgets.QVBoxLayout()

        # Labels
        self.hit_label = QtWidgets.QLabel("Waiting for hits...")
        self.hit_label.setFont(QtGui.QFont("Helvetica", 18))
        layout.addWidget(self.hit_label)

        self.avg_label = QtWidgets.QLabel("Rolling Average: -- ms")
        self.avg_label.setFont(QtGui.QFont("Helvetica", 14))
        self.avg_label.setStyleSheet("color: #00ff88;")
        layout.addWidget(self.avg_label)

        # Graph
        self.plot = pg.PlotWidget()
        self.plot.setBackground("#1e1e1e")
        self.plot.showGrid(x=True, y=True)
        self.plot.setYRange(-100, 100)  # ms early/late range
        self.curve = self.plot.plot(pen=None, symbol="o", symbolSize=8, symbolBrush="#ffaa00")
        layout.addWidget(self.plot)

        self.setLayout(layout)

    def update_display(self, error_ms, avg_error):
        direction = "early" if error_ms < 0 else "late"
        self.hit_label.setText(f"Hit: {error_ms:+.1f} ms {direction}")
        self.avg_label.setText(f"Rolling Average: ±{avg_error:.1f} ms")
        history.append(error_ms)
        if len(history) > 100:
            history.pop(0)
        self.curve.setData(list(range(len(history))), history)

# --- MIDI Thread ---
def listen_midi(app):
    global errors
    with mido.open_input(DEVICE_NAME) as inport:
        for msg in inport:
            if msg.type == "note_on" and msg.velocity > 0:
                hit_time = time.time()
                closest_beat = round((hit_time - start_time) / INTERVAL)
                expected_time = start_time + closest_beat * INTERVAL
                error_ms = (hit_time - expected_time + CALIBRATION_OFFSET) * 1000

                errors.append(abs(error_ms))
                if len(errors) > ROLLING_WINDOW:
                    errors.pop(0)
                avg_error = statistics.mean(errors)

                log_hit(error_ms, avg_error)

                # send update to GUI thread
                QtCore.QMetaObject.invokeMethod(
                    app, "update_display",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(float, error_ms),
                    QtCore.Q_ARG(float, avg_error)
                )

# --- Main ---
if __name__ == "__main__":
    threading.Thread(target=metronome, daemon=True).start()

    app = QtWidgets.QApplication([])
    window = AccuracyApp()
    window.show()

    midi_thread = threading.Thread(target=listen_midi, args=(window,), daemon=True)
    midi_thread.start()

    app.exec()