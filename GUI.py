import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

def open_window_directory():
    filename=filedialog.askopenfilename()
    return filename

# Initialize the main window
root = tk.Tk()
root.title('Audio Interface')
root.geometry('1200x700')
root.configure(bg='#1f003f')

# Sidebar Frame
sidebar = tk.Frame(root, bg='#1f003f', width=180)
sidebar.pack(side='left', fill='y')

# Folder Dropdown
folder_label = tk.Button(sidebar,text="📁", foreground="white",command=open_window_directory)

# Icons Frame
icons_frame = tk.Frame(sidebar, bg="#f4ebfd")
icons_frame.pack(pady=5, padx=5, anchor='nw')

# Waveform Display
waveform_frame = tk.Frame(root, bg='#e0f7fa', height=250, width=700)
waveform_frame.pack(pady=20)
tk.Label(waveform_frame, text='[Waveform]', bg='#e0f7fa', fg='black', font=('Arial', 24)).pack(expand=True)

# Playback Controls (Centered)
controls_frame = tk.Frame(root, bg='#1f003f')
controls_frame.pack(pady=5)
controls_inner = tk.Frame(controls_frame, bg='#1f003f')
controls_inner.pack()
for btn in ['⏪', '▶️', '⏩']:
    tk.Button(controls_inner, text=btn, font=('Arial', 24), bg='#e0f7fa', width=4).pack(side='left', padx=5)

# Lower Frame with Two Separate Parts
lower_frame = tk.Frame(root, bg='#1f003f')
lower_frame.pack(pady=20)

# Left and Right Subframes
left_frame = tk.Frame(lower_frame, bg='#1f003f')
left_frame.pack(side='left', padx=20)
right_frame = tk.Frame(lower_frame, bg='#1f003f')
right_frame.pack(side='right', padx=20)

# Buttons for Separate and Analyse
tk.Button(left_frame, text='Seperate', font=('Arial', 18), width=20, height=3, bg='#e0f7fa').pack()
tk.Button(right_frame, text='analyse', font=('Arial', 18), width=20, height=3, bg='#e0f7fa').pack()

root.mainloop()
