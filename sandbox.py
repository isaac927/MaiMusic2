import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os, threading, time
from pydub import AudioSegment
from pyaudio import PyAudio
from PIL import Image, ImageDraw, ImageTk
import numpy as np

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Login/Register Window ---
def show_login(root, on_success):
    login_win = tk.Toplevel(root)
    login_win.title("Login")
    login_win.geometry("300x200")
    login_win.resizable(False, False)
    login_win.grab_set()

    tk.Label(login_win, text="Username:").pack(pady=5)
    user_var = tk.StringVar()
    tk.Entry(login_win, textvariable=user_var).pack()

    tk.Label(login_win, text="Password:").pack(pady=5)
    pwd_var = tk.StringVar()
    tk.Entry(login_win, textvariable=pwd_var, show="*").pack()

    def do_login():
        u, p = user_var.get(), pwd_var.get()
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        if c.fetchone():
            conn.close()
            login_win.destroy()
            on_success()
        else:
            conn.close()
            messagebox.showerror("Login Failed", "Invalid credentials.")

    def do_register():
        username, password = user_var.get(), pwd_var.get()
        if not username or not password:
            messagebox.showwarning("Input Error", "Both fields are required.")
            return
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo("Success", "Registered! Now log in.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists.")
        conn.close()

    ttk.Button(login_win, text="Login", command=do_login).pack(pady=5)
    ttk.Button(login_win, text="Register", command=do_register).pack()
    login_win.mainloop()

# --- Audio Interface Setup ---
class AudioApp:
    def __init__(self, root):
        self.root = root
        self.init_audio_vars()
        self.build_ui()

    def init_audio_vars(self):
        self.audio_data = b''
        self.stream_pos = 0
        self.is_playing = False
        self.is_paused = False
        self.is_dragging = False
        self.chunk_size = 1024
        self.sound = AudioSegment.silent(duration=1000)
        self.audio_duration = 0

    def build_ui(self):
        self.root.title('Audio Interface')
        self.root.geometry('1200x500')
        self.root.configure(bg="#fbfbfb")
        self.root.resizable(False, False)

        sidebar = tk.Frame(self.root, bg="#484c80")
        sidebar.place(x=10, y=10, width=200, height=480)

        tk.Button(sidebar, text="📁", fg="white", bg="#484c80",
                  command=self.load_file).place(x=10, y=10, width=50, height=50)

        self.file_label = tk.Label(self.root, text="No file loaded")
        self.file_label.pack(pady=5)

        content_frame = tk.Frame(self.root, bg="#484c80")
        content_frame.place(x=220, y=10, width=970, height=300)

        pf = tk.Frame(content_frame, bg="#484c80")
        pf.pack(pady=20)

        self.progress_canvas = tk.Canvas(pf, width=300, height=20, bg="white", highlightthickness=1, highlightbackground="black")
        self.progress_canvas.pack()
        self.progress_fill = self.progress_canvas.create_rectangle(0,0,0,20, fill="green")

        self.progress_canvas.bind("<Button-1>", self.on_click)
        self.progress_canvas.bind("<B1-Motion>", self.on_drag)
        self.progress_canvas.bind("<ButtonRelease-1>", self.on_release)

        self.time_label = tk.Label(self.root, text="0 / 0 sec")
        self.time_label.pack()

        controls_frame = tk.Frame(content_frame, bg="#484c80")
        controls_frame.pack(pady=10)

        tk.Button(controls_frame, text="Rewind 5s", command=self.on_rewind).grid(row=0, column=0, padx=10)
        self.play_btn = tk.Button(controls_frame, text="▶️", command=self.on_play)
        self.play_btn.grid(row=0, column=1)
        tk.Button(controls_frame, text="Fast Forward 5s", command=self.on_fast_forward).grid(row=0, column=2, padx=10)

        option_frame = tk.Frame(self.root, bg="#d1d4f4")
        option_frame.place(x=220, y=320, width=970, height=170)
        tk.Button(option_frame, bg="#8d8e9f", text="SEPARATE", height=9, width=60).place(x=10, y=10)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
        if not file_path: return
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.mp3', '.wav']:
            messagebox.showerror("Invalid file", "Please choose .mp3 or .wav")
            return
        self.sound = AudioSegment.from_file(file_path)
        self.audio_data = self.sound.raw_data
        self.stream_pos = 0
        self.audio_duration = len(self.sound)
        self.file_label.config(text=os.path.basename(file_path))
        self.play_btn.config(text="▶️")
        self.update_progress_bar()

    def audio_loop(self):
        p = PyAudio()
        stream = p.open(format=p.get_format_from_width(self.sound.sample_width),
                        channels=self.sound.channels,
                        rate=self.sound.frame_rate,
                        output=True)
        while self.is_playing and self.stream_pos < len(self.audio_data):
            if self.is_paused or self.is_dragging:
                time.sleep(0.05)
                continue
            end = min(self.stream_pos + self.chunk_size, len(self.audio_data))
            stream.write(self.audio_data[self.stream_pos:end])
            self.stream_pos = end
            self.update_progress_bar()
        stream.stop_stream(); stream.close(); p.terminate()
        self.is_playing = False
        self.play_btn.config(text="▶️")

    def on_play(self):
        if not self.sound:
            messagebox.showerror("Error", "No file loaded.")
            return
        if self.is_playing:
            self.is_paused = True
            self.is_playing = False
            self.play_btn.config(text="▶️")
        else:
            self.is_paused = False
            self.is_playing = True
            threading.Thread(target=self.audio_loop, daemon=True).start()
            self.play_btn.config(text="⏸️")

    def on_rewind(self):
        self.stream_pos = max(0, self.stream_pos - int(5 * self.sound.frame_rate * self.sound.frame_width))
        self.update_progress_bar()

    def on_fast_forward(self):
        self.stream_pos = min(self.stream_pos + int(5 * self.sound.frame_rate * self.sound.frame_width), len(self.audio_data))
        self.update_progress_bar()

    def update_progress_bar(self):
        if not self.sound: return
        current_ms = self.stream_pos / (self.sound.frame_rate * self.sound.frame_width) * 1000
        progress = min(1.0, current_ms / self.audio_duration)
        width = self.progress_canvas.winfo_width()
        self.progress_canvas.coords(self.progress_fill, 0, 0, int(progress*width), 20)
        self.time_label.config(text=f"{int(current_ms // 1000)} / {int(self.audio_duration // 1000)} sec")

    def seek_to_position(self, x):
        width = self.progress_canvas.winfo_width()
        frac = min(max(x / width, 0), 1)
        new_ms = frac * self.audio_duration
        self.stream_pos = int((new_ms / 1000) * self.sound.frame_rate * self.sound.frame_width)
        self.update_progress_bar()

    def on_click(self, e):
        self.is_dragging = True
        self.seek_to_position(e.x)

    def on_drag(self, e):
        self.seek_to_position(e.x)

    def on_release(self, e):
        self.seek_to_position(e.x)
        self.is_dragging = False

# --- Run App ---
def main():
    root = tk.Tk()
    root.withdraw()
    def start_app():
        root.deiconify()
        AudioApp(root)
    show_login(root, start_app)
    root.mainloop()

if __name__ == "__main__":
    main()
