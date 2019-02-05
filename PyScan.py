import tkinter as tk

import sys
import os
import time

scanDir = os.getcwd()

def gen_filename():
    fn = os.path.join(scanDir, time.strftime("%Y%m%d-%H%M%S") + ".jpg")
    if os.path.exists(fn):
        raise Exception("File already exists: " + fn)
    return fn

def scan_4x6():
    fn = gen_filename()
    print("Scanning 4x6 to", fn)

def scan_5x7():
    fn = gen_filename()
    print("Scanning 5x7 to", fn)

def runGraphical():
    root = tk.Tk()
    root.title("Scan")

    frame = tk.Frame(root)
    frame.pack()

    label = tk.Label(
        frame,
        text="Choose scan size",
        fg="dark green")
    label.pack()

    b1 = tk.Button(
        frame,
        text="Scan 4x6",
        command=scan_4x6)
    b1.pack(side=tk.LEFT)

    b2 = tk.Button(
        frame,
        text="Scan 5x7",
        command=scan_5x7)
    b2.pack(side=tk.LEFT)

    q = tk.Button(
        frame,
        text="Exit",
        #fg="red",
        #command=quit)
        command=root.destroy)
    q.pack(side=tk.RIGHT)

    root.mainloop()

if __name__ == "__main__":
    print(gen_filename())
    runGraphical()
