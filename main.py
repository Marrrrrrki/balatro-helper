from __future__ import annotations
import argparse
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from ui.window import AdvisorWindow
from core.save_reader import find_steam_save

def main():
    parser = argparse.ArgumentParser(description="Read-only Balatro hand advisor")
    parser.add_argument("--save", type=Path, help="Path to a Balatro save.jkr")
    args = parser.parse_args()

    save_path = args.save or find_steam_save()
    root = tk.Tk()
    root.title("Balatro Advisor")
    root.geometry("1120x780")
    root.minsize(920, 660)
    app = AdvisorWindow(root, save_path)
    root.mainloop()

if __name__ == "__main__":
    main()
