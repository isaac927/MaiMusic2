import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import tkinter.font as tkFont
from tkinter import Canvas, Scrollbar
from pydub import AudioSegment
from pyaudio import PyAudio
from PIL import Image, ImageDraw, ImageTk
import numpy as np
import threading
import time

# Initialize global state
audio_data = b''
stream_pos = 0
is_playing = False
is_paused = False
play_thread = None
chunk_size = 1024
playhead = None
waveform_img = None
waveform_width = 0
sound = AudioSegment.silent(duration=1000)

# Audio Playback
def audio_loop():
    global stream_pos, is_playing
    p = PyAudio()
    stream = p.open(format=p.get_format_from_width(sound.sample_width),
                    channels=sound.channels,
                    rate=sound.frame_rate,
                    output=True)

    while is_playing and stream_pos < len(audio_data):
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

def update_playhead():
    if not is_playing:
        return
    elapsed = stream_pos / (sound.frame_rate * sound.frame_width)
    x = int((elapsed / (len(sound) / 1000)) * waveform_width)
    canvas.coords(playhead, x, 0, x, 200)
    canvas.after(30, update_playhead)

def restart_audio():
    global is_playing, play_thread
    if is_playing:
        is_playing = False
        time.sleep(0.1)
    is_playing = True
    play_thread = threading.Thread(target=audio_loop, daemon=True)
    play_thread.start()
    update_playhead()
    play_btn.config(text='⏸️')

def on_play():
    try:
        global is_playing, is_paused, audio_data, play_thread
        if is_playing:
            is_playing = False
            is_paused = True
            play_btn.config(text='▶️')
        else:
            audio_data = sound.raw_data
            is_playing = True
            is_paused = False
            play_thread = threading.Thread(target=audio_loop, daemon=True)
            play_thread.start()
            update_playhead()
            play_btn.config(text='⏸️')
    except Exception as e:
        messagebox.showerror("Error", "Please select an audio file first.")

def on_rewind():
    global stream_pos, is_playing
    try:
        stream_pos = max(0, stream_pos - int(5 * sound.frame_rate * sound.frame_width))
        restart_audio()
        is_playing = True
    except Exception as e:
        messagebox.showerror("Error", "Please select an audio file first.")

def on_fast_forward():
    try:
        global stream_pos, is_playing
        stream_pos = min(stream_pos + int(5 * sound.frame_rate * sound.frame_width), len(audio_data))
        restart_audio()
        is_playing = True
    except Exception as e:
        messagebox.showerror("Error", "Please select an audio file first.") 


def draw_waveform(audio_segment, width=3000, height=200):
    global waveform_img, playhead, waveform_width

    canvas.delete("all")

    samples = np.array(audio_segment.get_array_of_samples())
    samples = samples[::max(1, int(len(samples) / width))]
    max_amplitude = np.max(np.abs(samples))
    scale = height / 2 / max_amplitude

    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)
    for x, sample in enumerate(samples):
        y = int(sample * scale)
        draw.line([(x, height // 2), (x, height // 2 - y)], fill="black")

    waveform_img = ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, image=waveform_img, anchor='nw')
    waveform_width = width
    canvas.configure(scrollregion=(0, 0, waveform_width, height))
    playhead = canvas.create_line(0, 0, 0, 200, fill="red", width=2)

def open_window_directory():
    global sound, selected_file_label, audio_data, stream_pos

    file_path = filedialog.askopenfilename()
    if file_path:
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.mp3', '.wav']:
            messagebox.showerror("Invalid File", "Please select an MP3 or WAV file.")
            return

        try:
            selected_file_label.destroy()
        except Exception:
            pass

        selected_file_label = tk.Label(sidebar, text=os.path.basename(file_path), bg="#a5a7b8", fg="white", wraplength=180)
        selected_file_label.place(x=10, y=70, width=180, height=30)

        sound = AudioSegment.from_file(file_path)
        audio_data = sound.raw_data
        stream_pos = 0

        draw_waveform(sound)
        play_btn.config(text='▶️')

def spleeter_seperation(sound):
    pass
    # Placeholder for Spleeter separation logi

# --- GUI SETUP ---

# Main Window
root = tk.Tk()
root.title('Audio Interface')
root.geometry('1200x500')
root.configure(bg="#fbfbfb")
root.resizable(False, False)

# Sidebar
sidebar = tk.Frame(root, bg="#484c80")
sidebar.place(x=10, y=10, width=200, height=480)

# File Picker Button
folder_button_font = tkFont.Font(family="Arial", size=40, weight="bold")
folder_label = tk.Button(sidebar, text="📁", foreground="white", background="#484c80",command=open_window_directory, font=folder_button_font)
folder_label.place(x=10, y=10, width=50, height=50)

# Content Frame
content_frame = tk.Frame(root, bg="#484c80")
content_frame.place(x=220, y=10, width=970, height=300)

# Waveform Display
waveform_frame = tk.Frame(content_frame, bg="#fbfbfb")
waveform_frame.pack(fill="both", expand=True)

scroll_x = Scrollbar(waveform_frame, orient="horizontal")
scroll_x.pack(side="bottom", fill="x")

canvas = Canvas(waveform_frame, bg="white", height=150, xscrollcommand=scroll_x.set)
canvas.pack(side="top", fill="both", expand=True)
scroll_x.config(command=canvas.xview)

# Placeholder Text Before File is Loaded
placeholder_text = canvas.create_text(500, 75, text="Please select file", fill="black", font=("Arial", 20))

# Controls
controls_frame = tk.Frame(content_frame, bg="#484c80")
controls_frame.pack(pady=10)

rewind_btn = tk.Button(controls_frame, text="Rewind 5s", command=on_rewind)
rewind_btn.grid(row=0, column=0, padx=10, pady=5)

play_btn = tk.Button(controls_frame, text="▶️", command=on_play)
play_btn.grid(row=0, column=1)

fast_forward_btn = tk.Button(controls_frame, text="Fast Forward 5s", command=on_fast_forward)
fast_forward_btn.grid(row=0, column=2, padx=10, pady=5)

#option frame
option_frame = tk.Frame(root, bg="#d1d4f4")
option_frame.place(x=220, y=320, width=970, height=170)

seperate_function_button = tk.Button(option_frame,bg="#8d8e9f",text="SEPERATE",height=9, width=60)
seperate_function_button.place(x=10, y=10)

root.mainloop()