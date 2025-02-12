#!/usr/bin/env python

import tkinter as tk
from core.player import MusicPlayer
from tkinterdnd2 import TkinterDnD


def main():
    root = TkinterDnD.Tk()
    player = MusicPlayer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
