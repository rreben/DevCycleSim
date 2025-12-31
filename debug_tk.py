
import sys
import traceback

print("Python Executable:", sys.executable)
print("Python Version:", sys.version)

print("\n--- Attempting Imports ---")
try:
    print("Importing tkinter...")
    import tkinter as tk
    print("SUCCESS: tkinter imported. Version:", tk.TkVersion)

    print("Importing matplotlib...")
    import matplotlib
    print("SUCCESS: matplotlib imported. Version:", matplotlib.__version__)
    print("Matplotlib Backend:", matplotlib.get_backend())

    print("Importing backend_tkagg...")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    print("SUCCESS: FigureCanvasTkAgg imported.")

    print("\n--- Attempting Runtime Init ---")
    print("Creating root window...")
    root = tk.Tk()
    print("SUCCESS: Root window created.")
    root.destroy()
    print("SUCCESS: Root window destroyed.")

except Exception:
    print("\n!!! ERROR ENCOUNTERED !!!")
    traceback.print_exc()
