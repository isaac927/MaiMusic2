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
    """audio application class with playback, progress bar, and separation features"""

    def __init__(self, root):
        """initialize app"""
        self.root = root
        self.init_audio_vars()
        self.build_gui()

    def init_audio_vars(self):
        """initialize audio-related variables"""
        self.audio_data = None
        self.stream_pos = 0
        self.is_playing = False
        self.is_paused = False
        self.is_dragging = False
        self.chunk_size = 1024
        self.sound = AudioSegment.silent(duration=1000)
        self.audio_duration = 0

    def audio_loop(self):
        """audio playback loop"""
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

                if self.root.winfo_exists():
                    self.root.after(0, self.update_progress_bar)
                else:
                    break
        except Exception:
            messagebox.showerror("playback error", "please select an audio file")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            self.is_playing = False
            if self.root.winfo_exists():
                self.root.after(0, lambda: self.play_btn.config(text="▶️"))

    def on_play(self):
        """toggle play and pause"""
        try:
            if self.sound is None:
                messagebox.showerror("error", "no file loaded.")
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
        except Exception as e:
            messagebox.showerror("playback error", str(e))

    def on_rewind(self):
        """rewind audio by 5 seconds"""
        try:
            if self.sound:
                self.stream_pos = max(0, self.stream_pos - int(5 * self.sound.frame_rate * self.sound.frame_width))
                self.update_progress_bar()
        except Exception:
            messagebox.showerror("playback error", "please select an audio file")

    def on_fast_forward(self):
        """fast forward audio by 5 seconds"""
        try:
            if self.sound:
                self.stream_pos = min(self.stream_pos + int(5 * self.sound.frame_rate * self.sound.frame_width), len(self.audio_data))
                self.update_progress_bar()
        except Exception:
            messagebox.showerror("playback error", "please select an audio file")

    def update_progress_bar(self):
        """update progress bar and time label"""
        if not self.sound:
            return
        try:
            current_ms = self.stream_pos / (self.sound.frame_rate * self.sound.frame_width) * 1000
            progress = min(1.0, current_ms / self.audio_duration)
            bar_width = self.progress_canvas.winfo_width()
            self.progress_canvas.coords(self.progress_fill, 0, 0, int(progress * bar_width), 20)
            self.time_label.config(text=f"{int(current_ms // 1000)} / {int(self.audio_duration // 1000)} sec")
        except Exception:
            pass

    def seek_to_position(self, x):
        """seek audio to position"""
        if not self.sound:
            return
        bar_width = self.progress_canvas.winfo_width()
        fraction = min(max(x / bar_width, 0), 1)
        new_ms = fraction * self.audio_duration
        self.stream_pos = int((new_ms / 1000) * self.sound.frame_rate * self.sound.frame_width)
        self.update_progress_bar()

    def on_click(self, event):
        """handle click on progress bar"""
        self.is_dragging = True
        self.is_paused = True
        self.seek_to_position(event.x)

    def on_drag(self, event):
        """handle dragging on progress bar"""
        if self.is_dragging:
            self.seek_to_position(event.x)

    def on_release(self, event):
        """handle release after dragging on progress bar"""
        try:
            self.seek_to_position(event.x)
            self.is_dragging = False
            self.is_paused = False
        except Exception:
            pass

    def open_file_dialog(self):
        """open file dialog to select audio"""
        global file_name_label, file_path
        file_path = filedialog.askopenfilename(filetypes=[("audio files", "*.mp3 *.wav")])
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ['.mp3', '.wav']:
                messagebox.showerror("invalid file", "please choose .mp3 or .wav")
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
        """build main user interface"""
        global file_name_label, file_path
        self.root.title('audio interface')
        self.root.geometry('1200x500')
        self.root.configure(bg="#fbfbfb")
        self.root.resizable(False, False)

        sidebar = tk.Frame(self.root, bg="#252532")
        sidebar.place(x=10, y=10, width=200, height=480)

        folder_button_font = tkFont.Font(family="arial", size=40, weight="bold")
        folder_label = tk.Button(sidebar, text="📁", foreground="white", background="#484c80",
                                 command=self.open_file_dialog, font=folder_button_font)
        folder_label.place(x=10, y=10, width=50, height=50)

        self.file_label = tk.Label(self.root, text="no file loaded")
        self.file_label.pack(pady=5)

        self.content_frame = tk.Frame(self.root, bg="#484c80")
        self.content_frame.place(x=220, y=10, width=970, height=300)

        progress_frame = tk.Frame(self.content_frame, bg="#484c80")
        progress_frame.pack(pady=20)

        self.progress_canvas = tk.Canvas(progress_frame, width=300, height=20, bg="white", highlightthickness=1, highlightbackground="black")
        self.progress_canvas.grid(row=0)
        self.progress_fill = self.progress_canvas.create_rectangle(0, 0, 0, 20, fill="green")

        self.progress_canvas.bind("<Button-1>", self.on_click)
        self.progress_canvas.bind("<B1-Motion>", self.on_drag)
        self.progress_canvas.bind("<ButtonRelease-1>", self.on_release)

        self.time_label = tk.Label(progress_frame, text="0 / 0 sec")
        self.time_label.grid(row=1)

        controls_frame = tk.Frame(self.content_frame, bg="#484c80")
        controls_frame.pack(pady=10)

        rewind_btn = tk.Button(controls_frame, text="rewind 5s", command=self.on_rewind)
        rewind_btn.grid(row=0, column=0, padx=10, pady=5)

        self.play_btn = tk.Button(controls_frame, text="▶️", command=self.on_play)
        self.play_btn.grid(row=0, column=1)

        fast_forward_btn = tk.Button(controls_frame, text="fast forward 5s", command=self.on_fast_forward)
        fast_forward_btn.grid(row=0, column=2, padx=10, pady=5)

        file_name_label = tk.Label(self.content_frame, text="no file selected")
        file_name_label.pack()

        option_frame = tk.Frame(self.root, bg="#d1d4f4")
        option_frame.place(x=220, y=320, width=970, height=170)

        seperate_function_button = tk.Button(option_frame, bg="#8d8e9f", text="seperate", height=9, width=60,
                                             command=lambda: open_spleeter_window())
        seperate_function_button.place(x=10, y=10)

        def open_spleeter_window():
            """open spleeter separation window"""
            global file_path
            if 'file_path' not in globals() or not file_path:
                messagebox.showerror("error", "no audio file loaded. please load a file first.")
                return
            if not os.path.exists(file_path):
                messagebox.showerror("error", "selected audio file doesn't exist.")
                return

            seperate_function_button.config(state="disabled")

            new_window = tk.Toplevel(self.root)
            spleeter_seperation.spleeter_gui(new_window, file_path)

            def on_close():
                seperate_function_button.config(state="normal")
                new_window.destroy()
                self.output_screen(file_path)
            new_window.protocol("WM_DELETE_WINDOW", on_close)

    def output_screen(self, input_path):
        """show separated output screen"""
        for w in self.content_frame.winfo_children():
            w.destroy()

        base = os.path.splitext(os.path.basename(input_path))[0]
        sep_dir = os.path.join("output", "2stems", base)
        self.vocals_file = os.path.join(sep_dir, "vocals.wav")
        self.accomp_file = os.path.join(sep_dir, "accompaniment.wav")

        tk.Label(self.content_frame, text="separated output",
                 font=("arial", 14, "bold"), bg="#484c80", fg="white").pack(pady=5)

        import tkinter.ttk as ttk
        self.stem_choice = tk.StringVar(value="vocals")
        stem_box = ttk.Combobox(self.content_frame, textvariable=self.stem_choice,
                                values=["vocals", "accompaniment"], state="readonly", width=18)
        stem_box.pack(pady=5)
        stem_box.bind("<<ComboboxSelected>>", lambda e: self.load_output_audio())

        self.output_label = tk.Label(self.content_frame, text="", bg="#484c80", fg="white")
        self.output_label.pack()

        self.progress_canvas = tk.Canvas(self.content_frame, width=600, height=20,
                                         bg="white", highlightthickness=1, highlightbackground="black")
        self.progress_canvas.pack(pady=5)
        self.progress_fill = self.progress_canvas.create_rectangle(0, 0, 0, 20, fill="green")
        self.time_label = tk.Label(self.content_frame, text="0 / 0 sec", bg="#484c80", fg="white")
        self.time_label.pack()

        controls = tk.Frame(self.content_frame, bg="#484c80")
        controls.pack(pady=10)
        tk.Button(controls, text="⏪ 5s", command=self.on_rewind).pack(side="left", padx=5)
        self.play_btn = tk.Button(controls, text="▶️", command=self.on_play)
        self.play_btn.pack(side="left", padx=5)
        tk.Button(controls, text="⏩ 5s", command=self.on_fast_forward).pack(side="left", padx=5)

        tk.Button(self.content_frame, text="⬅ back", command=self.build_gui).pack(pady=5)

        self.load_output_audio()

    def load_output_audio(self):
        """load selected separated audio stem"""
        from pydub import AudioSegment
        choice = self.stem_choice.get()
        path = self.vocals_file if choice == "vocals" else self.accomp_file

        self.sound = AudioSegment.from_wav(path)
        self.audio_data = self.sound.raw_data
        self.audio_duration = len(self.sound)
        self.stream_pos = 0
        self.is_playing = False
        self.is_paused = False

        self.output_label.config(text=os.path.basename(path))
        self.play_btn.config(text="▶️")
        self.progress_canvas.coords(self.progress_fill, 0, 0, 0, 20)
        self.time_label.config(text=f"0 / {int(self.audio_duration // 1000)} sec")


def init_database():
    """initialize sqlite database for user accounts"""
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


def show_login(root, on_success):
    """show login/register window"""
    login_win = tk.Toplevel(root)
    login_win.title("login")
    login_win.geometry("300x200")
    login_win.resizable(False, False)
    login_win.grab_set()

    tk.Label(login_win, text="username:").pack(pady=5)
    user_var = tk.StringVar()
    tk.Entry(login_win, textvariable=user_var).pack()

    tk.Label(login_win, text="password:").pack(pady=5)
    pwd_var = tk.StringVar()
    tk.Entry(login_win, textvariable=pwd_var, show="*").pack()

    def do_login():
        """handle login"""
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
            messagebox.showerror("login failed", "invalid credentials.")

    def do_register():
        """handle registration"""
        u, p = user_var.get(), pwd_var.get()
        if not u or not p:
            messagebox.showwarning("input error", "both fields are required.")
            return
        connection = sqlite3.connect('users.db')
        c = connection.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, p))
            connection.commit()
            messagebox.showinfo("success", "registered! now log in.")
        except sqlite3.IntegrityError:
            messagebox.showerror("error", "username already exists.")
        connection.close()

    ttk.Button(login_win, text="login", command=do_login).pack(pady=5)
    ttk.Button(login_win, text="register", command=do_register).pack()


def main():
    """start the application"""
    init_database()
    root = tk.Tk()
    root.withdraw()

    def start_app():
        root.deiconify()
        app = audio_app(root)

    show_login(root, start_app)
    root.mainloop()


if __name__ == "__main__":
    main()
