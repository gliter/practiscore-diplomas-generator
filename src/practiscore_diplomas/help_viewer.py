"""Offline help bundled with both the Python package and Windows executable."""
from __future__ import annotations

import base64
from importlib.resources import files
import math
import re
from pathlib import Path
import sys
import tkinter as tk
from tkinter import font, ttk


def _help_directory(language: str):
    selected = language if language in ("pl", "en") else "en"
    filename = f"README.{selected}.md"
    if getattr(sys, "frozen", False):
        documentation = Path(sys.executable).resolve().parent / "docs" / filename
    else:
        documentation = Path(__file__).resolve().parents[2] / "docs" / filename
    if documentation.is_file():
        return documentation.parent
    return files("practiscore_diplomas").joinpath("docs")


def _load_help(language: str) -> str:
    selected = language if language in ("pl", "en") else "en"
    return _help_directory(language).joinpath(f"README.{selected}.md").read_text(encoding="utf-8")


def _help_photo(master: tk.Text, language: str, source: str, max_width: int) -> tk.PhotoImage:
    data = _help_directory(language).joinpath(source).read_bytes()
    picture = tk.PhotoImage(master=master, data=base64.b64encode(data).decode("ascii"))
    scale = max(1, math.ceil(picture.width() / max(1, max_width)))
    return picture.subsample(scale) if scale > 1 else picture


def _populate_help(text: tk.Text, content: str, language: str, max_width: int) -> list[tk.PhotoImage]:
    images = []
    in_code = False
    for line in content.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        image = re.fullmatch(r"\s*!\[([^\]]*)\]\(([^)]+)\)\s*", line)
        if in_code:
            text.insert("end", line + "\n", "code")
        elif image:
            caption, source = image.groups()
            try:
                picture = _help_photo(text, language, source, max_width)
                images.append(picture)
                text.image_create("end", image=picture)
                text.insert("end", "\n")
                if caption:
                    text.insert("end", caption + "\n", "caption")
            except (OSError, tk.TclError):
                label = "Nie można wyświetlić obrazka" if language == "pl" else "Could not display image"
                text.insert("end", f"{label}: {source}\n", "caption")
        elif line.startswith("# "):
            text.insert("end", line[2:] + "\n", "title")
        elif line.startswith("## "):
            text.insert("end", line[3:] + "\n", "heading")
        elif line.startswith("### "):
            text.insert("end", line[4:] + "\n", "subheading")
        elif line.startswith("|"):
            text.insert("end", line + "\n", "code")
        else:
            text.insert("end", line + "\n")
    return images


def show_help(parent: tk.Tk, language: str) -> tk.Toplevel:
    content = _load_help(language)
    polish = language == "pl"
    window = tk.Toplevel(parent)
    window.title("Pomoc — Dyplomy PractiScore" if polish else "Help — PractiScore Diplomas")
    width = min(980, max(1, window.winfo_screenwidth() - 100))
    height = min(760, max(1, window.winfo_screenheight() - 160))
    x = max(0, (window.winfo_screenwidth() - width) // 2)
    y = max(0, (window.winfo_screenheight() - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.minsize(min(640, width), min(400, height))
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)
    text = tk.Text(window, wrap="word", padx=22, pady=18, font="TkDefaultFont", relief="flat", borderwidth=0)
    scrollbar = ttk.Scrollbar(window, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=scrollbar.set)
    text.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    family = font.nametofont("TkDefaultFont").actual("family")
    text.tag_configure("title", font=(family, 17, "bold"), spacing1=10, spacing3=12)
    text.tag_configure("heading", font=(family, 12, "bold"), spacing1=12, spacing3=6)
    text.tag_configure("subheading", font=(family, 11, "bold"), spacing1=8, spacing3=4)
    text.tag_configure("code", font="TkFixedFont", background="#f1f3f5", lmargin1=12, lmargin2=12)
    text.tag_configure("caption", foreground="#606060", spacing3=12)
    # Tk stores image names only; keep the PhotoImage objects alive with the window.
    window.help_images = _populate_help(text, content, language, width - 70)
    text.configure(state="disabled")
    ttk.Button(window, text="Zamknij" if polish else "Close", command=window.destroy).grid(
        row=1, column=0, columnspan=2, padx=14, pady=12, sticky="e"
    )
    window.bind("<Escape>", lambda _event: window.destroy())
    text.focus_set()
    return window
