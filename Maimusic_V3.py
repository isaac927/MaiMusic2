import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import tkinter.font as tkFont
from pydub import AudioSegment
import pyaudio
import threading
import time
import sqlite3
import numpy as np
import spleeter_seperation

class audio_app:
    def __init__(self, root):
        self.root = root
        self.init_audio_vars()
        self.build_gui()

    def init_audio_vars(self):
        self.audio_data = None
        self.stream_pos = 0
        self.is_playing = False
        self.is_paused = False
        self.is_dragging = False
        self.chunk_size = 1024
        self.sound = AudioSegment.silent(duration=1000)
        self.audio_duration = 0

    def audio_loop(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=self.sound.channels,
                        rate=self.sound.frame_rate,
                        output=True,
                        frames_per_buffer=self.chunk_size)

        try:
            while self.is_playing and self.stream_pos < len(self.audio_data):
                if self.is_paused or self.is_dragging:
                    time.sleep(0.05)
                    continue
                end = min(self.stream_pos + self.chunk_size, len(self.audio_data))
                chunk = self.audio_data[self.stream_pos:end]
                stream.write(chunk)
                self.stream_pos = end

                # Schedule progress update safely in main thread
                if self.root.winfo_exists():
                    self.root.after(0, self.update_progress_bar)
                else:
                    break
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            self.is_playing = False
            if self.root.winfo_exists():
                self.root.after(0, lambda: self.play_btn.config(text="▶️"))

    def on_play(self):
        if self.sound is None:
            messagebox.showerror("Error", "No file loaded.")
            return

        if self.is_playing:
            self.is_paused = True
            self.is_playing = False
            self.play_btn.config(text="▶️")
        else:
            self.is_paused = False
            self.is_playing = True
            self.play_thread = threading.Thread(target=self.audio_loop, daemon=True)
            self.play_thread.start()
            self.play_btn.config(text="⏸️")

    def on_rewind(self):
        if self.sound:
            self.stream_pos = max(0, self.stream_pos - int(5 * self.sound.frame_rate * self.sound.frame_width))
            self.update_progress_bar()

    def on_fast_forward(self):
        if self.sound:
            self.stream_pos = min(self.stream_pos + int(5 * self.sound.frame_rate * self.sound.frame_width), len(self.audio_data))
            self.update_progress_bar()

    def update_progress_bar(self):
        if not self.sound:
            return
        current_ms = self.stream_pos / (self.sound.frame_rate * self.sound.frame_width) * 1000
        progress = min(1.0, current_ms / self.audio_duration)
        bar_width = self.progress_canvas.winfo_width()
        self.progress_canvas.coords(self.progress_fill, 0, 0, int(progress * bar_width), 20)
        self.time_label.config(text=f"{int(current_ms // 1000)} / {int(self.audio_duration // 1000)} sec")

    def seek_to_position(self, x):
        if not self.sound:
            return
        bar_width = self.progress_canvas.winfo_width()
        fraction = min(max(x / bar_width, 0), 1)
        new_ms = fraction * self.audio_duration
        self.stream_pos = int((new_ms / 1000) * self.sound.frame_rate * self.sound.frame_width)
        self.update_progress_bar()

    def on_click(self, event):
        self.is_dragging = True
        self.is_paused = True  # Pause playback while dragging
        self.seek_to_position(event.x)

    def on_drag(self, event):
        if self.is_dragging:
            self.seek_to_position(event.x)

    def on_release(self, event):
        self.seek_to_position(event.x)
        self.is_dragging = False
        self.is_paused = False  # Resume playback

    def open_file_dialog(self):
        global file_name_label, file_path
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
        if file_path:
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
            file_name_label.config(text=os.path.basename(file_path))
            self.update_progress_bar()

    

    def build_gui(self):
        global file_name_label, file_path
        self.root.title('Audio Interface')
        self.root.geometry('1200x500')
        self.root.configure(bg="#fbfbfb")
        self.root.resizable(False, False)

        sidebar = tk.Frame(self.root, bg="#484c80")
        sidebar.place(x=10, y=10, width=200, height=480)

        folder_button_font = tkFont.Font(family="Arial", size=40, weight="bold")
        folder_label = tk.Button(sidebar, text="📁", foreground="white", background="#484c80",
                                 command=self.open_file_dialog, font=folder_button_font)
        folder_label.place(x=10, y=10, width=50, height=50)

        self.file_label = tk.Label(self.root, text="No file loaded")
        self.file_label.pack(pady=5)

        content_frame = tk.Frame(self.root, bg="#484c80")
        content_frame.place(x=220, y=10, width=970, height=300)

        progress_frame = tk.Frame(content_frame, bg="#484c80")
        progress_frame.pack(pady=20)

        self.progress_canvas = tk.Canvas(progress_frame, width=300, height=20, bg="white",
                                         highlightthickness=1, highlightbackground="black")
        self.progress_canvas.grid(row=0)
        self.progress_fill = self.progress_canvas.create_rectangle(0, 0, 0, 20, fill="green")

        self.progress_canvas.bind("<Button-1>", self.on_click)
        self.progress_canvas.bind("<B1-Motion>", self.on_drag)
        self.progress_canvas.bind("<ButtonRelease-1>", self.on_release)

        self.time_label = tk.Label(progress_frame, text="0 / 0 sec")
        self.time_label.grid(row=1)

        controls_frame = tk.Frame(content_frame, bg="#484c80")
        controls_frame.pack(pady=10)

        rewind_btn = tk.Button(controls_frame, text="Rewind 5s", command=self.on_rewind)
        rewind_btn.grid(row=0, column=0, padx=10, pady=5)

        self.play_btn = tk.Button(controls_frame, text="▶️", command=self.on_play)
        self.play_btn.grid(row=0, column=1)

        fast_forward_btn = tk.Button(controls_frame, text="Fast Forward 5s", command=self.on_fast_forward)
        fast_forward_btn.grid(row=0, column=2, padx=10, pady=5)

        file_name_label = tk.Label(content_frame, text="no file selected")
        file_name_label.pack()

        option_frame = tk.Frame(self.root, bg="#d1d4f4")
        option_frame.place(x=220, y=320, width=970, height=170)

        seperate_function_button = tk.Button(option_frame, bg="#8d8e9f", text="SEPERATE", height=9, width=60,command=lambda: open_spleeter_window())
        seperate_function_button.place(x=10, y=10)

        def open_spleeter_window():
            global file_path

            # If no file picked, bail out
            if 'file_path' not in globals() or not file_path:
                messagebox.showerror("Error", "No audio file loaded. Please load a file first.")
                return
            if not os.path.exists(file_path):
                messagebox.showerror("Error", "Selected audio file doesn't exist.")
                return

            # Mark as open + disable the button
            seperate_function_button.config(state="disabled")

            # Create the child window
            new_window = tk.Toplevel(self.root)
            
            # Call to module from spleeter_seperation.py:
            spleeter_seperation.spleeter_gui(new_window, file_path)

            # When the user closes it, re-enable button & clear the flag
            def on_child_close():
                self.window_open = False
                seperate_function_button.config(state="normal")
                new_window.destroy()

            new_window.protocol("WM_DELETE_WINDOW", on_child_close)


# --- Database Setup ---
def init_database():
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
        u, p = user_var.get(), pwd_var.get()
        if not u or not p:
            messagebox.showwarning("Input Error", "Both fields are required.")
            return
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, p))
            conn.commit()
            messagebox.showinfo("Success", "Registered! Now log in.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists.")
        conn.close()

    ttk.Button(login_win, text="Login", command=do_login).pack(pady=5)
    ttk.Button(login_win, text="Register", command=do_register).pack()


# --- Run App ---
def main():
    init_database()
    root = tk.Tk()
    root.withdraw()  # Hide initially

    def start_app():
        root.deiconify()  # Show main app window
        app = audio_app(root)

    show_login(root, start_app)
    root.mainloop()


if __name__ == "__main__":
    main()
