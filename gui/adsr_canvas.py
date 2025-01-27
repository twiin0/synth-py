import tkinter as tk

MIN_ADSR_TIME = 0.01   # minimal nonzero Attack/Decay/Release
MIN_ADSR_SUSTAIN = 0.0 # minimal sustain, clamp to 1.0 max

class ADSRCanvas(tk.Canvas):
    """
    Straight-line ADSR with 4 draggable points: Attack, Decay, Sustain, Release.
    Numeric readouts updated in ModuleFrame.
    """
    def __init__(
        self,
        master,
        adsr_module,
        attack_var,
        decay_var,
        sustain_var,
        release_var,
        highlightbackground,
        width=160,
        height=100,
        **kwargs
    ):
        super().__init__(master, width=width, height=height, bg="#222222", highlightbackground=highlightbackground, **kwargs)
        self.adsr_module = adsr_module  # e.g. the ModuleFrame with set_global_attack/decay/etc.

        self.attack_var = attack_var
        self.decay_var = decay_var
        self.sustain_var = sustain_var
        self.release_var = release_var

        self.point_radius = 5
        self.width = width
        self.height = height

        # Hardcode the X positions for A, D, S, R
        self.Ax, self.Dx, self.Sx, self.Rx = 20, 60, 100, 140

        # Read initial times from the StringVars, clamp them
        try:
            att = float(self.attack_var.get())
        except:
            att = 0.01
        att = min(att, 5.0)

        try:
            dec = float(self.decay_var.get())
        except:
            dec = 0.1
        dec = min(dec, 5.0)

        try:
            sus = float(self.sustain_var.get())
        except:
            sus = 0.8
        if sus < 0.0:
            sus = 0.0
        if sus > 1.0:
            sus = 1.0

        try:
            rel = float(self.release_var.get())
        except:
            rel = 0.2
        rel = min(rel, 5.0)

        # Convert times/sustain to Y positions
        self.Ay = self.height - (att / 5.0 * self.height)  # Attack
        self.Dy = self.height - (dec / 5.0 * self.height)  # Decay
        self.Sy = self.height - (sus * self.height)        # Sustain
        self.Ry = self.height - (rel / 5.0 * self.height)  # Release

        self.line_id = None
        self.points = {}
        self._dragging = None

        # Bind mouse events
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)

        self.redraw()

    def redraw(self):
        self.delete("all")

        # Connect A -> D -> S -> R
        coords = [
            (self.Ax, self.Ay),
            (self.Dx, self.Dy),
            (self.Sx, self.Sy),
            (self.Rx, self.Ry)
        ]
        self.line_id = self.create_line(*coords, fill="white", smooth=False)

        # Draw the 4 draggable points
        self.points['A'] = self.create_oval(
            self.Ax - self.point_radius, self.Ay - self.point_radius,
            self.Ax + self.point_radius, self.Ay + self.point_radius,
            fill="#FF4040"
        )
        self.points['D'] = self.create_oval(
            self.Dx - self.point_radius, self.Dy - self.point_radius,
            self.Dx + self.point_radius, self.Dy + self.point_radius,
            fill="orange"
        )
        self.points['S'] = self.create_oval(
            self.Sx - self.point_radius, self.Sy - self.point_radius,
            self.Sx + self.point_radius, self.Sy + self.point_radius,
            fill="yellow"
        )
        self.points['R'] = self.create_oval(
            self.Rx - self.point_radius, self.Ry - self.point_radius,
            self.Rx + self.point_radius, self.Ry + self.point_radius,
            fill="#00C000"
        )

    def on_click(self, event):
        """
        Check which circle (A, D, S, or R) is clicked.
        """
        for key, item_id in self.points.items():
            x1, y1, x2, y2 = self.coords(item_id)
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self._dragging = key
                return

    def on_drag(self, event):
        if not self._dragging:
            return

        new_y = max(0, min(self.height, event.y))

        if self._dragging == 'A':
            self.Ay = new_y
            att = 5.0 * (1.0 - new_y / self.height)
            if att < 0.01:
                att = 0.01
            self.attack_var.set(f"{att:.2f}")

            if hasattr(self.adsr_module, 'set_global_attack'):
                self.adsr_module.set_global_attack(att)

        elif self._dragging == 'D':
            self.Dy = new_y
            dec = 5.0 * (1.0 - new_y / self.height)
            if dec < 0.01:
                dec = 0.01
            self.decay_var.set(f"{dec:.2f}")

            if hasattr(self.adsr_module, 'set_global_decay'):
                self.adsr_module.set_global_decay(dec)

        elif self._dragging == 'S':
            self.Sy = new_y
            sus = 1.0 - (new_y / self.height)
            if sus < 0.0:
                sus = 0.0
            if sus > 1.0:
                sus = 1.0
            self.sustain_var.set(f"{sus:.2f}")

            if hasattr(self.adsr_module, 'set_global_sustain'):
                self.adsr_module.set_global_sustain(sus)

        elif self._dragging == 'R':
            self.Ry = new_y
            rel = 5.0 * (1.0 - new_y / self.height)
            if rel < 0.01:
                rel = 0.01
            self.release_var.set(f"{rel:.2f}")

            if hasattr(self.adsr_module, 'set_global_release'):
                self.adsr_module.set_global_release(rel)

        self.redraw()
