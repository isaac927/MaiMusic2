import tkinter as tk
from tkinter import Canvas, Scrollbar
from pydub import AudioSegment
from pyaudio import PyAudio
from PIL import Image, ImageDraw, ImageTk
import numpy as np
import threading
import time

# Global audio state
audio_data = b''
stream_pos = 0
is_playing = False
is_paused = False
start_time = None
playhead = None
play_thread = None
chunk_size = 1024


def draw_waveform(audio_segment, width=3000, height=200):
    """Generate waveform with white background and black waveform."""
    samples = np.array(audio_segment.get_array_of_samples())
    samples = samples[::max(1, int(len(samples) / width))]

    max_amplitude = np.max(np.abs(samples))
    scale = height / 2 / max_amplitude

    img = Image.new("RGB", (width, height), color="white")  # White background
    draw = ImageDraw.Draw(img)

    for x, sample in enumerate(samples):
        y = int(sample * scale)
        draw.line([(x, height // 2), (x, height // 2 - y)], fill="black")  # Black waveform

    return img, ImageTk.PhotoImage(img), width


def update_playhead():
    if not is_playing:
        return

    if not is_paused:
        elapsed = (stream_pos / (sound.frame_rate * sound.frame_width))
        x = int((elapsed / duration_sec) * waveform_width)
        canvas.coords(playhead, x, 0, x, 200)

    canvas.after(30, update_playhead)


def audio_loop():
    global stream_pos, is_playing, is_paused

    p = PyAudio()
    stream = p.open(format=p.get_format_from_width(sound.sample_width),
                    channels=sound.channels,
                    rate=sound.frame_rate,
                    output=True)

    while stream_pos < len(audio_data):
        if is_paused:
            time.sleep(0.05)
            continue

        end = min(stream_pos + chunk_size, len(audio_data))
        chunk = audio_data[stream_pos:end]
        stream.write(chunk)
        stream_pos = end

    stream.stop_stream()
    stream.close()
    p.terminate()
    is_playing = False


def on_play():
    global is_playing, is_paused, stream_pos, audio_data, play_thread

    # If currently playing, stop and reset
    is_playing = False
    is_paused = False
    stream_pos = 0
    time.sleep(0.1)  # Short delay to ensure old thread ends

    # Restart playback
    is_playing = True
    audio_data = sound.raw_data
    play_thread = threading.Thread(target=audio_loop, daemon=True)
    play_thread.start()
    update_playhead()



def on_pause():
    global is_paused
    if is_playing:
        is_paused = not is_paused
        pause_btn.config(text="Resume" if is_paused else "Pause")


def on_fast_forward():
    global stream_pos
    if is_playing:
        advance = int(5 * sound.frame_rate * sound.frame_width)
        stream_pos = min(stream_pos + advance, len(audio_data))


# --- GUI Setup ---

root = tk.Tk()
root.title("Waveform Player")

frame = tk.Frame(root)
frame.pack(fill="both", expand=True)

scroll_x = Scrollbar(frame, orient="horizontal")
scroll_x.pack(side="bottom", fill="x")

canvas = Canvas(frame, bg="black", height=200, xscrollcommand=scroll_x.set)
canvas.pack(side="top", fill="both", expand=True)
scroll_x.config(command=canvas.xview)

# 🔊 Use a WAV file for reliable audio
sound = AudioSegment.from_mp3("input/sample.mp3") 
duration_sec = len(sound) / 1000
waveform_img_raw, waveform_img, waveform_width = draw_waveform(sound)

canvas.create_image(0, 0, image=waveform_img, anchor='nw')
canvas.configure(scrollregion=(0, 0, waveform_width, 200))
playhead = canvas.create_line(0, 0, 0, 200, fill="red", width=2)

# --- Control Buttons ---

controls = tk.Frame(root)
controls.pack(pady=10)

play_btn = tk.Button(controls, text="Play", command=on_play)
play_btn.pack(side="left", padx=5)

pause_btn = tk.Button(controls, text="Pause", command=on_pause)
pause_btn.pack(side="left", padx=5)

ff_btn = tk.Button(controls, text="Fast Forward 5s", command=on_fast_forward)
ff_btn.pack(side="left", padx=5)

root.mainloop()
