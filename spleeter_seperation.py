import tkinter as tk
from tkinter import messagebox
import os
import threading
import subprocess
import sys


class spleeter_gui:
    def __init__(self, root, audio_file, model_dir="pretrained_model"):
        self.root = root
        self.audio_file = audio_file
        self.model_dir = model_dir  # Local model path
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
        self.file_label = tk.Label(
            file_frame,
            text=os.path.basename(self.audio_file) if self.audio_file else "No file selected",
            fg="blue"
        )
        self.file_label.pack()

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
        self.start_btn.config(state="disabled")
        self.status_label.config(text="Processing...", fg="orange")
        threading.Thread(target=self.run_spleeter, daemon=True).start()

    def run_spleeter(self):
        try:
            stem = "2stems"
            output_dir = os.path.join(os.getcwd(), "output", stem)
            os.makedirs(output_dir, exist_ok=True)

            # Use local model
            env = os.environ.copy()
            if self.model_dir:
                env["MODEL_PATH"] = os.path.abspath(self.model_dir)

            cmd = [
                sys.executable, "-m", "spleeter", "separate",
                "-p", f"spleeter:{stem}",
                "-o", output_dir,
                self.audio_file
            ]
            subprocess.run(cmd, check=True, env=env)

            self.status_label.config(text=f"Done! Output in: {output_dir}", fg="green")
            messagebox.showinfo("Success", f"Separation completed! Files saved in:\n{output_dir}")
        except subprocess.CalledProcessError:
            self.status_label.config(text="Error during separation", fg="red")
            messagebox.showerror("Error", "Spleeter failed to process the file.")
        finally:
            self.start_btn.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    # Example usage — replace with the path to your audio file
    app = spleeter_gui(root, audio_file="output/sample3.mp3", model_dir="pretrained_model")
    root.mainloop()
