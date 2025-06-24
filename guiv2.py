from tkinter import *


dim_width = 1200
dim_height = 600
root = Tk()
root.title("Maimusic")
root.geometry(f'{dim_width}x{dim_height}')
root.configure(padx=10,pady=10,bg="white")
root.resizable(width=False,height=False)

sidebar = Frame(root, bg='#1f003f', width=dim_width/5, height=dim_height)
sidebar.place(x=0, y=0, width=dim_width/5, height=dim_height)

content_frame = Frame(root, bg="#ffffff", width=(dim_width/5)*4-30, height=dim_height, pady=10)
content_frame.place(x=dim_width/5, y=0, width=(dim_width/5)*4-30, height=dim_height)

option = Frame(content_frame, bg="#1f003f", height=290, width=(dim_width/5)*4-50)
option.place(x=0, y=0, width=(dim_width/5)*4-50, height=290)

view = Frame(content_frame, bg="#1f003f", height=250, width=(dim_width/5)*4-50)
view.place(x=0, y=100, width=(dim_width/5)*4-50, height=250)

root.mainloop()