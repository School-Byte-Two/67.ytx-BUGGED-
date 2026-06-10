import os
import glob
import threading
import winsound
import tkinter as tk
import random

stop_event = threading.Event()

TRAIL_LENGTH = 20
FRAME_MS = 50
WIN_SIZE = 90

trails = []
trails_lock = threading.Lock()


def make_67_window(root, x, y, alpha):
    win = tk.Toplevel(root)
    win.title("67")
    win.geometry(f"{WIN_SIZE}x{WIN_SIZE}+{int(x)}+{int(y)}")
    win.resizable(False, False)
    win.attributes("-topmost", True)
    win.attributes("-alpha", alpha)
    r = random.randint(180, 255)
    g = random.randint(0, 80)
    b = random.randint(0, 80)
    color = f"#{r:02x}{g:02x}{b:02x}"
    win.configure(bg=color)
    lbl = tk.Label(win, text="67", font=("Arial", WIN_SIZE // 3, "bold"),
                   bg=color, fg="white")
    lbl.pack(expand=True)
    win.protocol("WM_DELETE_WINDOW", lambda: None)
    return win


class Trail:
    def __init__(self, root, screen_w, screen_h):
        self.root = root
        self.sw = screen_w
        self.sh = screen_h
        self.windows = []

        # Tilfeldig startposisjon og retning
        self.x = random.randint(0, screen_w - WIN_SIZE)
        self.y = random.randint(0, screen_h - WIN_SIZE)
        speed = random.uniform(5, 12)
        angle = random.uniform(0, 360)
        import math
        self.vx = speed * math.cos(math.radians(angle))
        self.vy = speed * math.sin(math.radians(angle))

    def step(self):
        if stop_event.is_set():
            self.cleanup()
            return

        # Flytt
        self.x += self.vx
        self.y += self.vy

        # Bounce på kantene
        if self.x < 0:
            self.x = 0
            self.vx = abs(self.vx)
        elif self.x > self.sw - WIN_SIZE:
            self.x = self.sw - WIN_SIZE
            self.vx = -abs(self.vx)

        if self.y < 0:
            self.y = 0
            self.vy = abs(self.vy)
        elif self.y > self.sh - WIN_SIZE - 40:
            self.y = self.sh - WIN_SIZE - 40
            self.vy = -abs(self.vy)

        # Nytt vindu fremst
        win = make_67_window(self.root, self.x, self.y, 1.0)
        self.windows.insert(0, win)

        # Oppdater gjennomsiktighet på eldre vinduer
        for i, w in enumerate(self.windows):
            try:
                w.attributes("-alpha", max(0.08, 1.0 - i * 0.05))
            except Exception:
                pass

        # Fjern eldste vindu
        if len(self.windows) > TRAIL_LENGTH:
            old = self.windows.pop()
            try:
                old.destroy()
            except Exception:
                pass

        self.root.after(FRAME_MS, self.step)

    def cleanup(self):
        for w in self.windows:
            try:
                w.destroy()
            except Exception:
                pass
        self.windows.clear()


def spam_wav():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    wav_files = glob.glob(os.path.join(script_dir, "*.wav"))
    if not wav_files:
        return
    while not stop_event.is_set():
        for wav_file in wav_files:
            if stop_event.is_set():
                break
            winsound.PlaySound(wav_file, winsound.SND_FILENAME)


def add_trail(root, sw, sh):
    t = Trail(root, sw, sh)
    with trails_lock:
        trails.append(t)
    root.after(0, t.step)


def main():
    root = tk.Tk()
    root.withdraw()

    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()

    # Kontrollvindu
    ctrl = tk.Toplevel(root)
    ctrl.title("67 KONTROLL")
    ctrl.geometry("200x110+10+10")
    ctrl.attributes("-topmost", True)
    ctrl.protocol("WM_DELETE_WINDOW", lambda: None)
    ctrl.resizable(False, False)

    tk.Label(ctrl, text="67 Spammer", font=("Arial", 11, "bold")).pack(pady=(8, 2))

    btn_frame = tk.Frame(ctrl)
    btn_frame.pack(pady=4)

    tk.Button(btn_frame, text="+1 Spor", font=("Arial", 11, "bold"),
              bg="#2196F3", fg="white", width=8,
              command=lambda: add_trail(root, sw, sh)).pack(side="left", padx=6)

    tk.Button(btn_frame, text="STOPP", font=("Arial", 11, "bold"),
              bg="red", fg="white", width=8,
              command=lambda: stop_event.set()).pack(side="left", padx=6)

    # Start med 1 spor
    add_trail(root, sw, sh)

    # Lyd
    threading.Thread(target=spam_wav, daemon=True).start()

    # Sjekk stopp
    def check_stop():
        if stop_event.is_set():
            with trails_lock:
                for t in trails:
                    t.cleanup()
            try:
                ctrl.destroy()
            except Exception:
                pass
            root.quit()
        else:
            root.after(200, check_stop)

    root.after(200, check_stop)
    root.mainloop()
    print("Ferdig.")


if __name__ == "__main__":
    main()
