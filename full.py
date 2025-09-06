import mido
import time
import threading
import playsound3
from playsound3 import playsound
import statistics


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

def listen_midi():
    """Listen for pad hits and calculate timing error relative to nearest tick."""
    global errors

    with mido.open_input(DEVICE_NAME) as inport:
        for msg in inport:
            if msg.type == "note_on" and msg.velocity > 0:
                hit_time = time.time()
                closest_beat = round((hit_time - start_time) / INTERVAL)
                expected_time = start_time + closest_beat * INTERVAL

                # apply calibration
                error_ms = (hit_time - expected_time + CALIBRATION_OFFSET) * 1000
                direction = "early" if error_ms < 0 else "late"
                print(f"Pad hit: {error_ms:+.1f} ms {direction}")

                # update rolling error window
                errors.append(abs(error_ms))
                if len(errors) > ROLLING_WINDOW:
                    errors.pop(0)

                # calculate rolling average
                avg_error = statistics.mean(errors)
                print(f"Rolling average (last {len(errors)} hits): ±{avg_error:.1f} ms")

                # log every full window
                if len(errors) == ROLLING_WINDOW:
                    log_to_file(avg_error)

if __name__ == "__main__":
    # Start metronome in background
    threading.Thread(target=metronome, daemon=True).start()

    print("Listening for pad hits... (Ctrl+C to quit)")
    print(f"Calibration offset: {CALIBRATION_OFFSET*1000:.0f} ms\n")
    print(f"Rolling average window: {ROLLING_WINDOW} hits")
    print(f"Logs will be saved in: {LOG_FILE}\n")
    listen_midi()