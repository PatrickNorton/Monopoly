# Plz use this to create a frontend
import tkinter as tk
root = tk.Tk()
logo = tk.PhotoImage(file='Monopolyboard.jpg')
logo = logo.zoom(2)
logo = logo.subsample(5)
w = tk.Label(root, image=logo)
w.pack()
root.mainloop()
