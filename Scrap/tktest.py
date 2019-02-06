import tkinter as tk

root = tk.Tk()

def A():
    little = tk.Label(root, text="Little")
    bigger = tk.Label(root, text='Much bigger label')
    little.grid(column=0,row=0)
    bigger.grid(column=0,row=0)
    root.after(2000, lambda: little.lift())

class Callback:
    def __init__(self, size):
        self.size = size
    def fn(self):
        print("Button pressed for", self.size)
        xy = self.size.split("x")
        x = int(float(xy[0]) * 300)
        y = int(float(xy[1]) * 300)
        print(x, y)

def B():
    for size in ["5x3.5", "6x4", "7x5"]:
        tk.Button(root, text="Scan " + size, command=Callback(size).fn).pack(side=LEFT)

    tk.Label(root, text="Custom size:").pack(side=LEFT)
    custom = tk.Entry(root)
    custom.pack(side=LEFT)
    tk.Button(root, text="Scan", command=lambda: Callback(custom.get()).fn()).pack(side=LEFT)

def C():
    tk.Label(root, text="Landscape:").grid(row=0, column=0, padx=5, pady=5)
    tk.Label(root, text="Portrait:").grid(row=1, column=0, padx=5, pady=5)
    tk.Label(root, text="Custom size:").grid(row=2, column=0, padx=5, pady=5)

    for row, sizes in enumerate([
        ["5 x 3.5", "6 x 4", "7 x 5"],
        ["3.5 x 5", "4 x 6", "5 x 7"]]):
        for col, size in enumerate(sizes):
            tk.Button(root, text=size, command=Callback(size).fn).grid(row=row, column=col+1, padx=5, pady=5)
    custom = tk.Entry(root, width=8)
    custom.insert(0, "2x3")
    custom.grid(row=2, column=1, padx=5, pady=5)
    tk.Button(root, text="Scan", command=lambda: Callback(custom.get()).fn()).grid(row=2, column=3, padx=5, pady=5)

    tk.Button(root, text='Quit', command=root.quit).grid(row=3, column=0, padx=5, pady=5)

C()
root.mainloop()
