import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import tkinter.font as tkFont

# List to hold file names
file_list=[]


def list_files():
    for item in file_list:
        tk.Button(sidebar,text=item, foreground="black",background="#ffffff",width=50).pack(side="top",padx=5,anchor="w")    

def open_window_directory():
    filename = filedialog.askopenfilename()
    if filename:
        file_list.append(filename)
        update_display(sidebar)
        print(file_list)

def update_display(sidebar):
    # Remove all widgets except the folder button and icons_frame
    for widget in sidebar.winfo_children():
        # Keep the folder button and icons_frame
        if isinstance(widget, tk.Button) and widget.cget("text") == "📁":
            continue
        if isinstance(widget, tk.Frame):
            continue
        widget.destroy()
    # Re-add file buttons
    list_files()

# Initialize the main window

root = tk.Tk()
root.title('Audio Interface')
root.geometry('1200x700')
root.configure(bg='#1f003f')

# Sidebar Frame
sidebar = tk.Frame(root, bg='#1f003f', width=180)
sidebar.pack(side='left', fill='y')

#file dialouge open""
folder_button_font = tkFont.Font(family="Arial", size=40, weight="bold")
folder_label = tk.Button(sidebar,text="📁", foreground="white",background="#1f003f",command=open_window_directory,font=folder_button_font)
folder_label.pack(side="top")

list_files()

# Waveform Display
waveform_frame = tk.Frame(root, bg="#23cbe1", height=250, width=700)
waveform_frame.pack(pady=20)
tk.Label(waveform_frame, text='[Waveform]', bg='#e0f7fa', fg='black', font=('Arial', 24)).pack(expand=True)

# Playback Controls (Centered)
controls_frame = tk.Frame(root, bg="#7d38c1")
controls_frame.pack(pady=5)
controls_inner = tk.Frame(controls_frame, bg='#1f003f')
controls_inner.pack()
for btn in ['⏪', '▶️', '⏩']:
    tk.Button(controls_inner, text=btn, font=('Arial', 24), bg='#e0f7fa', width=4).pack(side='left', padx=5)

# Lower Frame with Two Separate Parts
lower_frame = tk.Frame(root, bg="#a2a920")
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