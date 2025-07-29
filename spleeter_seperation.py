import tkinter as tk
from tkinter import messagebox, ttk
import os
import threading
import subprocess
import sys

class spleeter_gui:
    def __init__(self, root, audio_file):
        self.root = root
        self.audio_file = audio_file  # Provided from main program
        self.root.title("Spleeter Stem Separation")
        self.root.geometry("500x250")
        self.root.resizable(False, False)

        self.stem_choice = tk.StringVar(value="2stems")

        self.build_gui()

    def build_gui(self):
        # File Display
        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=10)

        tk.Label(file_frame, text="File to separate:").pack()
        self.file_label = tk.Label(file_frame, text=os.path.basename(self.audio_file), fg="blue")
        self.file_label.pack()

        # Stem Selection
        stem_frame = tk.LabelFrame(self.root, text="Choose Stem Option")
        stem_frame.pack(pady=10, padx=20, fill="x")

        tk.Radiobutton(stem_frame, text="2 Stems (Vocals + Accompaniment)", variable=self.stem_choice, value="2stems").pack(anchor="w")
        tk.Radiobutton(stem_frame, text="4 Stems (Vocals + Drums + Bass + Other)", variable=self.stem_choice, value="4stems").pack(anchor="w")
        tk.Radiobutton(stem_frame, text="5 Stems (Vocals + Drums + Bass + Piano + Other)", variable=self.stem_choice, value="5stems").pack(anchor="w")

        # Start Button
        self.start_btn = tk.Button(self.root, text="Start Separation", command=self.confirm_and_run)
        self.start_btn.pack(pady=10)

        # Status
        self.status_label = tk.Label(self.root, text="Idle", fg="green")
        self.status_label.pack(pady=5)

    def confirm_and_run(self):
        if not self.audio_file:
            messagebox.showerror("Error", "No audio file provided.")
            return

        confirm = messagebox.askyesno("Download Warning",
                                      '''Spleeter will download a large pretrained model if not cached.
                                    The higher the stem, the larger the model will be. Continue?''')
        if confirm:
            self.start_btn.config(state="disabled")
            self.status_label.config(text="Processing...", fg="orange")
            threading.Thread(target=self.run_spleeter, daemon=True).start()

    def run_spleeter(self):
        try:
            stem = self.stem_choice.get()
            output_dir = os.path.join(os.path.dirname(self.audio_file), f"output_{stem}")

            cmd = [
                sys.executable, '-m', 'spleeter', 'separate',
                '-p', f'spleeter:{stem}',
                '-o', output_dir,
                self.audio_file
            ]
            subprocess.run(cmd, check=True)

            self.status_label.config(text=f"Done! Output in: {output_dir}", fg="green")
            messagebox.showinfo("Success", f"Separation completed! Files saved in:\n{output_dir}")
        except subprocess.CalledProcessError:
            self.status_label.config(text="Error during separation", fg="red")
            messagebox.showerror("Error", "Spleeter failed to process the file.")
        finally:
            self.start_btn.config(state="normal")

