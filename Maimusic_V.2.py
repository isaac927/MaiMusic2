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
class audio_app:
    def __init__(self,root):
        # Initialize global state
        self.root = root
        self.root.title('Audio Interface')
        self.root.geometry('1200x500')
        self.build_gui()
        self.audio_data = b''
        self.stream_pos = 0
        self.is_playing = False
        self.is_paused = False
        self.play_thread = None
        self.chunk_size = 1024
        self.sound = AudioSegment.silent(duration=1000)
        self.is_dragging = False

    # Audio Playback
    def audio_loop(self):
        global stream_pos, is_playing
        p = PyAudio()
        stream = p.open(format=p.get_format_from_width(sound.sample_width),
                        channels=sound.channels,
                        rate=sound.frame_rate,
                        output=True)

        while is_playing and stream_pos < len(audio_data):
            if is_paused or is_dragging:  # pause audio output during drag
                time.sleep(0.05)
                continue
            end = min(stream_pos + self.chunk_size, len(audio_data))
            chunk = audio_data[stream_pos:end]
            stream.write(chunk)
            stream_pos = end
            self.update_progress_bar()

        stream.stop_stream()
        stream.close()
        p.terminate()
        is_playing = False
        play_btn.config(text="▶️")

    def on_play(self):
        global is_playing, is_paused, stream_pos, play_thread
        if sound is None:
            messagebox.showerror("Error", "No file loaded.")
            return

        if is_playing:
            is_paused = True
            is_playing = False
            play_btn.config(text="▶️")
        else:
            is_paused = False
            is_playing = True
            play_thread = threading.Thread(target=self.audio_loop, daemon=True)
            play_thread.start()
            play_btn.config(text="⏸️")

    def on_rewind(self):
        global stream_pos
        if sound:
            stream_pos = max(0, stream_pos - int(5 * sound.frame_rate * sound.frame_width))
            self.update_progress_bar()

    def on_fast_forward(self):
        global stream_pos
        if sound:
            stream_pos = min(stream_pos + int(5 * sound.frame_rate * sound.frame_width), len(audio_data))
            self.update_progress_bar()

    def load_file(self):
        global sound, audio_data, stream_pos, audio_duration
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ['.mp3', '.wav']:
                messagebox.showerror("Invalid file", "Please choose .mp3 or .wav")
                return

            sound = AudioSegment.from_file(file_path)
            audio_data = sound.raw_data
            stream_pos = 0
            audio_duration = len(sound)  # in ms
            file_label.config(text=os.path.basename(file_path))
            play_btn.config(text="▶️")
            self.update_progress_bar()

    def update_progress_bar(self):
        if not sound:
            return
        current_ms = stream_pos / (sound.frame_rate * sound.frame_width) * 1000
        progress = min(1.0, current_ms / audio_duration)
        bar_width = progress_canvas.winfo_width()
        progress_canvas.coords(progress_fill, 0, 0, int(progress * bar_width), 20)
        time_str = f"{int(current_ms // 1000)} / {int(audio_duration // 1000)} sec"
        time_label.config(text=time_str)

    def seek_to_position(self,x):
        global stream_pos
        if not sound:
            return
        bar_width = progress_canvas.winfo_width()
        fraction = min(max(x / bar_width, 0), 1)
        new_ms = fraction * audio_duration
        stream_pos = int((new_ms / 1000) * sound.frame_rate * sound.frame_width)
        self.update_progress_bar()

    def on_click(self,event):
        global is_dragging
        is_dragging = True
        self.seek_to_position(event.x)

    def on_drag(self,event):
        self.seek_to_position(event.x)

    def on_release(self,event):
        global is_dragging
        self.seek_to_position(event.x)
        is_dragging = False

    def open_file_dialog(self):
        global sound, audio_data, stream_pos, audio_duration
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio Files", "*.mp3 *.wav")]
        )
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ['.mp3', '.wav']:
                messagebox.showerror("Invalid File", "Please select an MP3 or WAV file.")
                return
            sound = AudioSegment.from_file(file_path)
            audio_data = sound.raw_data
            stream_pos = 0
            audio_duration = len(sound)  # in milliseconds
            file_label.config(text=os.path.basename(file_path))
            play_btn.config(text="▶️")
            self.update_progress_bar()



    def spleeter_seperation(self,sound):
        pass
        # Placeholder for Spleeter separation logi

    # --- GUI SETUP ---

    # Main Window
    def build_gui(self):
        global root, file_label, play_btn, progress_canvas, progress_fill, time_label
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
        folder_label = tk.Button(sidebar, text="📁", foreground="white", background="#484c80",command=self.open_file_dialog, font=folder_button_font)
        folder_label.place(x=10, y=10, width=50, height=50)

        # File Label
        file_label = tk.Label(root, text="No file loaded")
        file_label.pack(pady=5)

        # Content Frame
        content_frame = tk.Frame(root, bg="#484c80")
        content_frame.place(x=220, y=10, width=970, height=300)

        # Audio Display
        progress_frame = tk.Frame(content_frame, bg="#484c80")
        progress_frame.pack(pady=20)

        progress_canvas = tk.Canvas(progress_frame, width=300, height=20, bg="white", highlightthickness=1, highlightbackground="black")
        progress_canvas.pack()
        progress_fill = progress_canvas.create_rectangle(0, 0, 0, 20, fill="green")

        progress_canvas.bind("<Button-1>", self.on_click)
        progress_canvas.bind("<B1-Motion>", self.on_drag)
        progress_canvas.bind("<ButtonRelease-1>", self.on_release)

        time_label = tk.Label(root, text="0 / 0 sec")
        time_label.pack()



        # Controls
        controls_frame = tk.Frame(content_frame, bg="#484c80")
        controls_frame.pack(pady=10)

        rewind_btn = tk.Button(controls_frame, text="Rewind 5s", command=self.on_rewind)
        rewind_btn.grid(row=0, column=0, padx=10, pady=5)

        play_btn = tk.Button(controls_frame, text="▶️", command=self.on_play)
        play_btn.grid(row=0, column=1)

        fast_forward_btn = tk.Button(controls_frame, text="Fast Forward 5s", command=self.on_fast_forward)
        fast_forward_btn.grid(row=0, column=2, padx=10, pady=5)

        #option frame
        option_frame = tk.Frame(root, bg="#d1d4f4")
        option_frame.place(x=220, y=320, width=970, height=170)

        seperate_function_button = tk.Button(option_frame,bg="#8d8e9f",text="SEPERATE",height=9, width=60)
        seperate_function_button.place(x=10, y=10)