import math
import customtkinter
import tkinter as tk

from gui.adsr_canvas import ADSRCanvas

# If your module classes are in "modules", adjust accordingly
from modules import (
    PolySynthModule,
    LowPassFilterModule,
    HighPassFilterModule,
    TremoloModule,
    VibratoModule,
    ArpeggiatorModule
)

class ModuleFrame(customtkinter.CTkFrame):
    """
    Unified UI for each module.

    If user chooses an oscillator wave ("Sine","Square","Sawtooth","Triangle"),
    build a “poly synth” style UI with frequency slider + wave preview + ADSR on the right.
    If user chooses "Low-Pass Filter","High-Pass Filter","Tremolo","Vibrato",
    we show the appropriate controls (cutoff sliders, effect depth/frequency, etc.).
    Now, if the user selects "Arpeggiator" we show a simple arpeggiator UI.
    """
    def __init__(self, parent_gui, module_type, audio_manager, **kwargs):
        super().__init__(parent_gui.staging_area, **kwargs)
        self.parent_gui = parent_gui
        self.module_type = module_type.lower()
        self.audio_manager = audio_manager

        # Shared slider vars for filters/effects
        self.slider_var1 = tk.DoubleVar()
        self.slider_label_var1 = tk.StringVar(value="0.0")
        self.slider_var2 = tk.DoubleVar()
        self.slider_label_var2 = tk.StringVar(value="0.0")

        # ADSR numeric readouts
        self.attack_var = tk.StringVar(value="0.01")
        self.decay_var = tk.StringVar(value="0.10")
        self.sustain_var = tk.StringVar(value="0.80")
        self.release_var = tk.StringVar(value="0.20")

        # Create the actual module instance
        self.module = self.create_module(self.module_type)
        # Insert it into the chain
        self.audio_manager.module_chain_manager.add_module(self.module)
        self.configure(
            fg_color="#666666", 
            corner_radius=6,
            width=360, 
            height=270
        )
        self.pack_propagate(False)

        # Determine title color based on module type
        title_color = self.get_colour(self.module_type)

        # Create title frame with a specific border (outline) color
        self.title_frame = customtkinter.CTkFrame(
            self,
            fg_color=title_color,
            border_color=title_color,
            border_width=2,
            corner_radius=6
        )
        self.title_frame.pack(fill="x", padx=0, pady=(5,2))

        # Create and pack the title label
        self.title_label = customtkinter.CTkLabel(
            self.title_frame,
            text=module_type,
            text_color="white",
            font=("Arial", 12)
        )
        self.title_label.pack(padx=5, pady=5)

        # Build UI based on type
        if any(x in self.module_type for x in ["sine", "triangle", "square", "sawtooth", "poly", "synth"]):
            self.build_poly_synth_ui()
        elif "low-pass" in self.module_type:
            self.build_lpf_ui()
        elif "high-pass" in self.module_type:
            self.build_hpf_ui()
        elif "tremolo" in self.module_type:
            self.build_tremolo_ui()
        elif "vibrato" in self.module_type:
            self.build_vibrato_ui()
        elif "arpeggiator" in self.module_type:
            self.build_arpeggiator_ui()

        # Move Left / Move Right buttons
        self.move_left_button = customtkinter.CTkButton(
            self, text="←", width=30, fg_color="#888888",
            command=self.move_left
        )
        self.move_left_button.pack(side="left", padx=2)

        self.move_right_button = customtkinter.CTkButton(
            self, text="→", width=30, fg_color="#888888",
            command=self.move_right
        )
        self.move_right_button.pack(side="left", padx=2)
        
        # Remove button
        self.remove_button = customtkinter.CTkButton(
            self, text="Remove", fg_color="gray",
            command=self.remove_self
        )
        self.remove_button.pack(side="bottom", pady=5)

    def get_colour(self, module_type: str) -> str:
        """
        Returns a hexadecimal color for the title frame based on the module type.
        You can customize these colors as needed.
        """
        # Define color mappings for groups of module types
        if any(x in module_type for x in ["sine", "triangle", "square", "sawtooth", "poly", "synth"]):
            # Oscillators
            return "#1E90FF"  # DodgerBlue
        elif "low-pass" in module_type or "high-pass" in module_type:
            # Filters
            return "#32CD32"  # LimeGreen
        elif "tremolo" in module_type or "vibrato" in module_type:
            # Effects
            return "#FF8C00"  # DarkOrange
        elif "arpeggiator" in module_type:
            # Arpeggiator
            return "#9932CC"  # DarkOrchid
        else:
            # Default color if none of the above match
            return "#FFFFFF"  # white
        
    def create_module(self, module_type_str):
        """
        Map the user's selection to a module class.
        """
        if "sine" in module_type_str:
            return PolySynthModule(sample_rate=44100, max_voices=8, waveform="sine")
        elif "triangle" in module_type_str:
            return PolySynthModule(sample_rate=44100, max_voices=8, waveform="triangle")
        elif "sawtooth" in module_type_str:
            return PolySynthModule(sample_rate=44100, max_voices=8, waveform="sawtooth")
        elif "square" in module_type_str:
            return PolySynthModule(sample_rate=44100, max_voices=8, waveform="square")
        elif "low-pass" in module_type_str:
            return LowPassFilterModule(cutoff=1000.0, sample_rate=44100)
        elif "high-pass" in module_type_str:
            return HighPassFilterModule(cutoff=500.0, sample_rate=44100)
        elif "tremolo" in module_type_str:
            return TremoloModule(sample_rate=44100, depth=0.5, lfo_rate=5.0, wave='sine')
        elif "vibrato" in module_type_str:
            return VibratoModule(sample_rate=44100, base_delay_ms=10.0, depth_ms=5.0, lfo_rate=5.0, wave='sine')
        elif "arpeggiator" in module_type_str:
            return ArpeggiatorModule(note_callback=self.audio_manager.keyboard_handler.handle_note, sample_rate=44100, mode="up", rate=6.0, hold=False)
        else:
            # fallback => poly synth with no wave
            return PolySynthModule(sample_rate=44100, max_voices=8, waveform="none")
        
    def move_left(self):
        """
        Swap this module with the previous one in self.parent_gui.staging_modules
        and do the same in audio_manager.module_chain.
        Then refresh the staging layout.
        """
        frames = self.parent_gui.staging_modules
        chain = self.audio_manager.module_chain_manager.module_chain

        current_index = frames.index(self)
        if current_index > 0:
            # swap in the frames list
            frames[current_index], frames[current_index - 1] = (
                frames[current_index - 1], frames[current_index]
            )

            # also swap in the audio_manager's module_chain
            mod_index = chain.index(self.module)
            if mod_index > 0:
                chain[mod_index], chain[mod_index - 1] = (
                    chain[mod_index - 1], chain[mod_index]
                )

            self.parent_gui.refresh_staging_layout()

    def move_right(self):
        """
        Swap this module with the next one in the staging list
        and also swap in audio_manager.module_chain.
        """
        frames = self.parent_gui.staging_modules
        chain = self.audio_manager.module_chain_manager.module_chain

        current_index = frames.index(self)
        if current_index < len(frames) - 1:
            # swap in the frames list
            frames[current_index], frames[current_index + 1] = (
                frames[current_index + 1], frames[current_index]
            )

            # swap in the module_chain
            mod_index = chain.index(self.module)
            if mod_index < len(chain) - 1:
                chain[mod_index], chain[mod_index + 1] = (
                    chain[mod_index + 1], chain[mod_index]
                )

            self.parent_gui.refresh_staging_layout()
            
    def remove_self(self):
        if self.module in self.audio_manager.module_chain_manager.module_chain:
            self.audio_manager.module_chain_manager.module_chain.remove(self.module)
        self.parent_gui.remove_module(self)

    # ---------------------------------------------------------
    # 1) "Poly Synth" UI 
    # ---------------------------------------------------------
    def build_poly_synth_ui(self):
        container = customtkinter.CTkFrame(
            self, 
            fg_color="#666666"
        )
        container.pack(fill="both", expand=True, padx=5, pady=5)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        # Left side: freq slider + wave preview
        left_frame = customtkinter.CTkFrame(container, fg_color="#666666")
        left_frame.grid(row=0, column=0, sticky="nsw", padx=(0,5))

        freq_label = customtkinter.CTkLabel(
            left_frame, 
            text="Frequency:", 
            text_color="white"
        )
        freq_label.pack()
        self.freq_var = tk.DoubleVar(value=440.0)
        self.freq_display_var = tk.StringVar(value="440.0")

        freq_slider = customtkinter.CTkSlider(
            left_frame, 
            from_=0.0, to=2000, number_of_steps=2000,
            variable=self.freq_var,
            command=self.on_freq_change,
            width=110
        )
        freq_slider.pack(padx=5, pady=5)

        freq_display_lbl = customtkinter.CTkLabel(
            left_frame, 
            textvariable=self.freq_display_var, 
            text_color="white"
        )
        freq_display_lbl.pack()

        self.wave_canvas_width = 160
        self.wave_canvas_height = 80
        self.wave_canvas = tk.Canvas(
            left_frame, 
            width=self.wave_canvas_width, 
            height=self.wave_canvas_height,
            bg="#222222", 
            highlightthickness=1,
            highlightbackground=self.get_colour(self.module_type)
        )
        self.wave_canvas.pack(pady=5)
        self.draw_waveform()

        # Right side: ADSR
        right_frame = customtkinter.CTkFrame(
            container, 
            fg_color="#555555"
        )
        right_frame.grid(row=0, column=1, sticky="nsew")

        adsr_label = customtkinter.CTkLabel(
            right_frame, 
            text="ADSR:", 
            text_color="white"
        )
        adsr_label.pack()

        self.adsr_canvas = ADSRCanvas(
            right_frame,
            adsr_module=self,
            attack_var=self.attack_var,
            decay_var=self.decay_var,
            sustain_var=self.sustain_var,
            release_var=self.release_var,
            highlightbackground=self.get_colour(self.module_type),
            width=150, 
            height=80
        )
        self.adsr_canvas.pack(padx=5, pady=5)

        readout_frame = customtkinter.CTkFrame(right_frame, fg_color="#666666")
        readout_frame.pack(pady=2)
        labA = customtkinter.CTkLabel(readout_frame, textvariable=self.attack_var, width=30, text_color="#FF4040")
        labA.grid(row=0, column=0, padx=2)
        labD = customtkinter.CTkLabel(readout_frame, textvariable=self.decay_var, width=30, text_color="orange")
        labD.grid(row=0, column=1, padx=2)
        labS = customtkinter.CTkLabel(readout_frame, textvariable=self.sustain_var, width=30, text_color="yellow")
        labS.grid(row=0, column=2, padx=2)
        labR = customtkinter.CTkLabel(readout_frame, textvariable=self.release_var, width=30, text_color="#00C000")
        labR.grid(row=0, column=3, padx=2)

    # ---------------------------------------------------------
    # 2) Low-Pass Filter UI
    # ---------------------------------------------------------
    def build_lpf_ui(self):  # NEEDS WORK
        lbl = customtkinter.CTkLabel(self, text="Cutoff:", text_color="white")
        lbl.pack(pady=(5,2))

        self.slider_var1.set(1000.0)
        self.slider_label_var1.set("1000.0")

        cutoff_slider = customtkinter.CTkSlider(
            self, from_=1, to=2000, number_of_steps=20000,
            variable=self.slider_var1,
            command=self.on_lpf_cutoff_change,
            width=110
        )
        cutoff_slider.pack(padx=5, pady=5)

        numeric_lbl = customtkinter.CTkLabel(
            self, textvariable=self.slider_label_var1, text_color="white"
        )
        numeric_lbl.pack()

        self.lpf_canvas_width = 160
        self.lpf_canvas_height = 80
        self.lpf_canvas = tk.Canvas(
            self, 
            width=self.lpf_canvas_width, 
            height=self.lpf_canvas_height,
            bg="#222222", 
            highlightthickness=1,
            highlightbackground=self.get_colour(self.module_type)
        )
        self.lpf_canvas.pack(pady=5)
        self.draw_lpf_curve()

    def draw_lpf_curve(self):  # NEEDS WORK
        self.lpf_canvas.delete("all")
        cutoff = float(self.slider_var1.get())

        w = self.lpf_canvas_width
        h = self.lpf_canvas_height
        
        c_log = math.log10(cutoff)
        min_log, max_log = math.log10(50), math.log10(10000)
        frac = (c_log - min_log) / (max_log - min_log)
        knee_x = frac * w

        num_points = 50
        points = []
        for i in range(num_points):
            x = i * (w/(num_points-1))
            if x < knee_x:
                y = 0.3 * h
            else:
                ratio = (x - knee_x) / max(1, (w - knee_x))
                y = 0.3 * h + 0.5 * h * ratio
            points.append((x, y))

        flat_pts = []
        for (xv, yv) in points:
            flat_pts.extend([xv, yv])

        self.lpf_canvas.create_line(flat_pts, fill="white", width=2, smooth=True)

    def on_lpf_cutoff_change(self, val):  # NEEDS WORK
        c = float(val)
        self.slider_label_var1.set(f"{c:.1f}")
        if hasattr(self.module, 'set_cutoff'):
            self.module.set_cutoff(c)
        self.draw_lpf_curve()

    # ---------------------------------------------------------
    # 3) High-Pass Filter UI
    # ---------------------------------------------------------
    def build_hpf_ui(self):  # NEEDS WORK
        lbl = customtkinter.CTkLabel(self, text="Cutoff:", text_color="white")
        lbl.pack(pady=(5,2))

        self.slider_var1.set(500.0)
        self.slider_label_var1.set("500.0")

        cutoff_slider = customtkinter.CTkSlider(
            self, from_=1, to=2000, number_of_steps=20000,
            variable=self.slider_var1,
            command=self.on_hpf_cutoff_change,
            width=110
        )
        cutoff_slider.pack(padx=5, pady=5)

        numeric_lbl = customtkinter.CTkLabel(
            self, textvariable=self.slider_label_var1, text_color="white"
        )
        numeric_lbl.pack()

        self.hpf_canvas_width = 160
        self.hpf_canvas_height = 80
        self.hpf_canvas = tk.Canvas(
            self, 
            width=self.hpf_canvas_width, 
            height=self.hpf_canvas_height,
            bg="#222222", 
            highlightthickness=1,
            highlightbackground=self.get_colour(self.module_type)
        )
        self.hpf_canvas.pack(pady=5)
        self.draw_hpf_curve()

    def draw_hpf_curve(self):  # NEEDS WORK
        self.hpf_canvas.delete("all")
        cutoff = float(self.slider_var1.get())

        w = self.hpf_canvas_width
        h = self.hpf_canvas_height
        c_log = math.log10(cutoff)
        min_log, max_log = math.log10(20), math.log10(5000)
        frac = (c_log - min_log) / (max_log - min_log)
        knee_x = frac * w

        num_points = 50
        points = []
        for i in range(num_points):
            x = i * (w / (num_points - 1))
            if x < knee_x:
                ratio = (x / max(1, knee_x))
                y = 0.7 * h - 0.4 * h * ratio
            else:
                y = 0.3 * h
            points.append((x, y))

        flat_pts = []
        for (xv, yv) in points:
            flat_pts.extend([xv, yv])

        self.hpf_canvas.create_line(flat_pts, fill="white", width=2, smooth=True)

    def on_hpf_cutoff_change(self, val):  # NEEDS WORK
        c = float(val)
        self.slider_label_var1.set(f"{c:.1f}")
        if hasattr(self.module, 'set_cutoff'):
            self.module.set_cutoff(c)
        self.draw_hpf_curve()

    # ---------------------------------------------------------
    # 4) Tremolo UI
    # ---------------------------------------------------------
    def build_tremolo_ui(self):
        container = customtkinter.CTkFrame(self, fg_color="#666666")
        container.pack(fill="both", expand=True, padx=5, pady=5)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        # LEFT FRAME (Wave Type + Canvas)
        left_frame = customtkinter.CTkFrame(container, fg_color="#666666")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        wave_type_label = customtkinter.CTkLabel(left_frame, text="Wave Type:", text_color="white")
        wave_type_label.pack(pady=(5, 2))

        allowed_waves = ['sine', 'square', 'triangle', 'sawtooth']
        self.tremolo_wave_var = tk.StringVar(value=allowed_waves[0])  # default: 'sine'

        wave_type_menu = customtkinter.CTkOptionMenu(
            left_frame,
            variable=self.tremolo_wave_var,
            values=allowed_waves,
            command=self.on_tremolo_wave_type_change,
            width=120
        )
        wave_type_menu.pack(padx=5, pady=3)

        # Canvas for LFO shape
        self.tremolo_canvas_width = 160
        self.tremolo_canvas_height = 80
        self.tremolo_canvas = tk.Canvas(
            left_frame,
            width=self.tremolo_canvas_width,
            height=self.tremolo_canvas_height,
            bg="#222222", 
            highlightthickness=1,
            highlightbackground=self.get_colour(self.module_type)
        )
        self.tremolo_canvas.pack(pady=(5, 10))

        # RIGHT FRAME (Depth + Rate Sliders)
        right_frame = customtkinter.CTkFrame(container, fg_color="#666666")
        right_frame.grid(row=0, column=1, sticky="nsew")

        # Depth
        depth_label = customtkinter.CTkLabel(right_frame, text="Depth:", text_color="white")
        depth_label.pack(pady=(5, 2))

        self.slider_var1.set(0.6)
        self.slider_label_var1.set("0.6")

        depth_slider = customtkinter.CTkSlider(
            right_frame,
            from_=0.0, to=1.0,
            variable=self.slider_var1,
            command=self.on_tremolo_depth_change,
            width=110
        )
        depth_slider.pack(padx=5)

        depth_value_lbl = customtkinter.CTkLabel(
            right_frame,
            textvariable=self.slider_label_var1,
            text_color="white"
        )
        depth_value_lbl.pack(pady=(0, 10))

        # Rate
        rate = customtkinter.CTkLabel(right_frame, text="Rate:", text_color="white")
        rate.pack(pady=(0, 2))

        self.slider_var2.set(5.0)
        self.slider_label_var2.set("5.0")

        rate_slider = customtkinter.CTkSlider(
            right_frame,
            from_=0.1, to=10.0,
            variable=self.slider_var2,
            command=self.on_tremolo_rate_change,
            width=110
        )
        rate_slider.pack(padx=5)

        rate_value_lbl = customtkinter.CTkLabel(
            right_frame,
            textvariable=self.slider_label_var2,
            text_color="white"
        )
        rate_value_lbl.pack(pady=(0, 10))

        # Draw initial wave
        self.tremolo_canvas.after(100, lambda: self.draw_lfo_waveform(
            canvas=self.tremolo_canvas,
            wave_type=self.tremolo_wave_var.get(),
            rate=self.slider_var2.get(),
            depth=self.slider_var1.get()
        ))

    def on_tremolo_depth_change(self, val):
        d = float(val)
        self.slider_label_var1.set(f"{d:.2f}")
        if hasattr(self.module, 'set_depth'):
            self.module.set_depth(d)
        self.draw_lfo_waveform(
            canvas=self.tremolo_canvas,
            wave_type=self.tremolo_wave_var.get(),
            rate=self.slider_var2.get(),
            depth=self.slider_var1.get()
        )

    def on_tremolo_rate_change(self, val):
        fr = float(val)
        self.slider_label_var2.set(f"{fr:.2f}")
        if hasattr(self.module, 'set_rate'):
            self.module.set_rate(fr)
        self.draw_lfo_waveform(
            canvas=self.tremolo_canvas,
            wave_type=self.tremolo_wave_var.get(),
            rate=self.slider_var2.get(),
            depth=self.slider_var1.get()
        )

    def on_tremolo_wave_type_change(self, selected_wave: str):
        if hasattr(self.module, 'set_wave_type'):
            self.module.set_wave_type(selected_wave)
        self.draw_lfo_waveform(
            canvas=self.tremolo_canvas,
            wave_type=self.tremolo_wave_var.get(),
            rate=self.slider_var2.get(),
            depth=self.slider_var1.get()
        )

    # ---------------------------------------------------------
    # 5) Vibrato UI
    # ---------------------------------------------------------
    def build_vibrato_ui(self):
        container = customtkinter.CTkFrame(
            self, 
            fg_color="#666666"
        )
        container.pack(fill="both", expand=True, padx=5, pady=5)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        # LEFT FRAME (Wave Type + Canvas)
        left_frame = customtkinter.CTkFrame(
            container, 
            fg_color="#666666"
        )
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        wave_type_label = customtkinter.CTkLabel(
            left_frame, 
            text="Wave Type:", 
            text_color="white"
        )
        wave_type_label.pack(pady=(5, 2))

        allowed_waves = ['sine', 'square', 'triangle', 'sawtooth']
        self.vibrato_wave_var = tk.StringVar(value=allowed_waves[0])  # default: 'sine'

        wave_type_menu = customtkinter.CTkOptionMenu(
            left_frame,
            variable=self.vibrato_wave_var,
            values=allowed_waves,
            command=self.on_vibrato_wave_type_change,
            width=120
        )
        wave_type_menu.pack(padx=5, pady=3)

        # Canvas for LFO shape
        self.vibrato_canvas_width = 160
        self.vibrato_canvas_height = 80
        self.vibrato_canvas = tk.Canvas(
            left_frame,
            width=self.vibrato_canvas_width,
            height=self.vibrato_canvas_height,
            bg="#222222", 
            highlightthickness=1,
            highlightbackground=self.get_colour(self.module_type)
        )
        self.vibrato_canvas.pack(pady=(5, 10))

        # RIGHT FRAME (Depth + Rate Sliders)
        right_frame = customtkinter.CTkFrame(container, fg_color="#666666")
        right_frame.grid(row=0, column=1, sticky="nsew")

        # Depth (ms)
        depth_label = customtkinter.CTkLabel(right_frame, text="Depth (ms):", text_color="white")
        depth_label.pack(pady=(5, 2))

        self.slider_var1.set(1.0)
        self.slider_label_var1.set("1.0")

        depth_slider = customtkinter.CTkSlider(
            right_frame,
            from_=0.0, to=1.0,
            variable=self.slider_var1,
            command=self.on_vibrato_depth_change,
            width=110
        )
        depth_slider.pack(padx=5)

        depth_value_lbl = customtkinter.CTkLabel(
            right_frame,
            textvariable=self.slider_label_var1,
            text_color="white"
        )
        depth_value_lbl.pack(pady=(0, 10))

        # Rate (Hz)
        rate_label = customtkinter.CTkLabel(right_frame, text="Rate (Hz):", text_color="white")
        rate_label.pack(pady=(0, 2))

        self.slider_var2.set(6.0)
        self.slider_label_var2.set("6.0")

        rate_slider = customtkinter.CTkSlider(
            right_frame,
            from_=0.1, to=10.0,
            variable=self.slider_var2,
            command=self.on_vibrato_rate_change,
            width=110
        )
        rate_slider.pack(padx=5)

        rate_value_lbl = customtkinter.CTkLabel(
            right_frame,
            textvariable=self.slider_label_var2,
            text_color="white"
        )
        rate_value_lbl.pack(pady=(0, 10))

        # Draw initial wave
        self.vibrato_canvas.after(100, lambda: self.draw_lfo_waveform(
            canvas=self.vibrato_canvas,
            wave_type=self.vibrato_wave_var.get(),
            rate=self.slider_var2.get(),
            depth=self.slider_var1.get()
        ))

    def on_vibrato_depth_change(self, val):
        depth = float(val)
        self.slider_label_var1.set(f"{depth:.2f}")
        if hasattr(self.module, 'set_depth_ms'):
            self.module.set_depth_ms(depth)
        self.draw_lfo_waveform(
            canvas=self.vibrato_canvas,
            wave_type=self.vibrato_wave_var.get(),
            rate=self.slider_var2.get(),
            depth=self.slider_var1.get()
        )

    def on_vibrato_rate_change(self, val):
        rate = float(val)
        self.slider_label_var2.set(f"{rate:.2f}")
        if hasattr(self.module, 'set_rate'):
            self.module.set_rate(rate)
        self.draw_lfo_waveform(
            canvas=self.vibrato_canvas,
            wave_type=self.vibrato_wave_var.get(),
            rate=self.slider_var2.get(),
            depth=self.slider_var1.get()
        )

    def on_vibrato_wave_type_change(self, selected_wave: str):
        if hasattr(self.module, 'set_wave_type'):
            self.module.set_wave_type(selected_wave)
        self.draw_lfo_waveform(
            canvas=self.vibrato_canvas,
            wave_type=self.vibrato_wave_var.get(),
            rate=self.slider_var2.get(),
            depth=self.slider_var1.get()
        )
        
    def draw_lfo_waveform(self, canvas, wave_type, rate, depth):
        """
        Draw a cycle (or multiple cycles) of an LFO waveform, incorporating 'rate' and 'depth'.
        """
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        canvas.delete("all")

        num_points = 200
        points = []
        for i in range(num_points):
            t = i / (num_points - 1)
            angle = 2.0 * math.pi * rate * t

            if wave_type == "sine":
                raw_val = math.sin(angle)
            elif wave_type == "square":
                raw_val = 1.0 if math.sin(angle) >= 0 else -1.0
            elif wave_type == "triangle":
                raw_val = (2.0 / math.pi) * math.asin(math.sin(angle))
            elif wave_type == "sawtooth":
                frac = (rate * t) % 1.0
                raw_val = 2.0 * frac - 1.0
            else:
                raw_val = 0.0
            
            y = depth * raw_val  
            x_canvas = t * w
            y_canvas = (1.0 - y) * (h / 2.0)
            points.append((x_canvas, y_canvas))

        flat_pts = []
        for (xx, yy) in points:
            flat_pts.extend([xx, yy])

        canvas.create_line(flat_pts, fill="white", width=2, smooth=True)

    # ---------------------------------------------------------
    # 6) Arpeggiator UI
    # ---------------------------------------------------------
    def build_arpeggiator_ui(self):
        """
        Build a simple UI for the arpeggiator. Includes:
        - Pattern selection
        - Simple preview
        - Rate slider
        - A toggle button for hold On/Off
        """
        container = customtkinter.CTkFrame(self, fg_color="#666666")
        container.pack(fill="both", expand=True, padx=5, pady=5)
        container.grid_columnconfigure((0, 1), weight=1)

        # ─────────────────────────────────────────────────────────
        # Left Frame: Pattern selection + preview
        # ─────────────────────────────────────────────────────────
        left_frame = customtkinter.CTkFrame(container, fg_color="#666666")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        mode_label = customtkinter.CTkLabel(left_frame, text="Mode:", text_color="white")
        mode_label.pack(pady=(5, 2))

        allowed_modes = ["Up", "Down", "UpDown", "Random"]
        self.arpeggio_mode_var = tk.StringVar(value=allowed_modes[0])

        mode_menu = customtkinter.CTkOptionMenu(
            left_frame,
            variable=self.arpeggio_mode_var,
            values=allowed_modes,
            command=self.on_arpeggio_mode_change,
            width=120
        )
        mode_menu.pack(padx=5, pady=3)

        self.arpeggiator_canvas_width = 160
        self.arpeggiator_canvas_height = 80
        self.arpeggiator_canvas = tk.Canvas(
            left_frame,
            width=self.arpeggiator_canvas_width,
            height=self.arpeggiator_canvas_height,
            bg="#222222",
            highlightthickness=1,
            highlightbackground=self.get_colour(self.module_type)
        )
        self.arpeggiator_canvas.pack(pady=(5, 10))
        self.draw_arpeggiator_preview()

        # ─────────────────────────────────────────────────────────
        # Right Frame: Rate slider + Hold toggle button
        # ─────────────────────────────────────────────────────────
        right_frame = customtkinter.CTkFrame(container, fg_color="#666666")
        right_frame.grid(row=0, column=1, sticky="nsew")

        tempo_label = customtkinter.CTkLabel(right_frame, text="Rate:", text_color="white")
        tempo_label.pack(pady=(5, 2))

        self.tempo_var = tk.DoubleVar(value=5.0)
        self.tempo_label_var = tk.StringVar(value="5.0")

        tempo_slider = customtkinter.CTkSlider(
            right_frame,
            from_=0, to=20,
            variable=self.tempo_var,
            command=self.on_tempo_change,
            width=110
        )
        tempo_slider.pack(padx=5, pady=5)

        tempo_value_lbl = customtkinter.CTkLabel(right_frame, textvariable=self.tempo_label_var, text_color="white")
        tempo_value_lbl.pack(pady=(0, 10))

        # ─────────────────────────────────────────────────────────
        # Add a button to toggle hold ON/OFF
        # ─────────────────────────────────────────────────────────
        self.hold_var = False  # track current state locally

        self.hold_button = customtkinter.CTkButton(
            right_frame,
            text="Hold: OFF",           # initial label
            command=self.toggle_hold,   # callback below
            fg_color="#444444"
        )
        self.hold_button.pack(pady=(0, 10))

    def toggle_hold(self):
        """
        Toggles the 'hold' state and updates the ArpeggiatorModule via self.module.set_hold(...)
        """
        self.hold_var = not self.hold_var
        if self.hold_var:
            self.hold_button.configure(text="Hold: ON")
        else:
            self.hold_button.configure(text="Hold: OFF")

        if hasattr(self.module, "set_hold"):
            self.module.set_hold(self.hold_var)


    def on_tempo_change(self, val):
        tempo = float(val)
        self.tempo_label_var.set(f"{tempo:.1f}")
        if hasattr(self.module, 'set_rate'):
            self.module.set_rate(tempo)

    def on_arpeggio_mode_change(self, selected_mode: str):
        if hasattr(self.module, 'set_mode'):
            # Send a lower-case value to the module (if that’s how you intend to use it)
            self.module.set_mode(selected_mode.lower())
        self.draw_arpeggiator_preview()

    def draw_arpeggiator_preview(self):
        """
        A simple preview for the arpeggiator that just displays the selected pattern.
        """
        self.arpeggiator_canvas.delete("all")
        pattern = self.arpeggio_mode_var.get()
        w = self.arpeggiator_canvas_width
        h = self.arpeggiator_canvas_height
        self.arpeggiator_canvas.create_text(w/2, h/2, text=f"Pattern: {pattern}", fill="white", font=("Arial", 12))

    # ---------------------------------------------------------
    # Frequency slider + wave preview for "Poly Synth"
    # ---------------------------------------------------------
    def on_freq_change(self, val):
        freq_float = float(val)
        if hasattr(self, 'freq_display_var'):
            self.freq_display_var.set(f"{freq_float:.1f}")
        if hasattr(self.module, "set_frequency"):
            self.module.set_frequency(freq_float)
        self.draw_waveform()

    def draw_waveform(self):
        if not hasattr(self, 'wave_canvas'):
            return

        self.wave_canvas.delete("all")

        freq = float(self.freq_var.get()) if hasattr(self, 'freq_var') else 440.0
        waveform = getattr(self.module, 'waveform', 'sine')
        time_window = 0.01
        num_points = 200
        w = self.wave_canvas_width
        h = self.wave_canvas_height
        points = []

        for i in range(num_points):
            t = (i/(num_points-1))*time_window
            if waveform == "sine":
                y = math.sin(2.0*math.pi*freq*t)
            elif waveform == "square":
                s = math.sin(2.0*math.pi*freq*t)
                y = 9.99 if s>=0 else -9.99
            elif waveform == "triangle":
                y = (2.0/math.pi)*math.asin(math.sin(2.0*math.pi*freq*t))
            elif waveform == "sawtooth":
                frac = (freq*t)-math.floor(freq*t)
                y = 2.0*frac - 1.0
            else:
                y=0.0

            x_canvas = i*(w/(num_points-1))
            y_canvas = (1.0-y)*(h/2.0)
            points.append((x_canvas,y_canvas))

        flat_pts = []
        for (xv,yv) in points:
            flat_pts.extend([xv,yv])

        self.wave_canvas.create_line(flat_pts, fill="white", width=2, smooth=True)

    # ---------------------------------------------------------
    # ADSRCanvas -> these calls go to module.set_adsr(...)
    # ---------------------------------------------------------
    def set_global_attack(self, val):
        try:
            a = float(val)
        except:
            a = 0.01
        if hasattr(self.module, 'set_adsr'):
            d = getattr(self.module, 'global_decay', 0.1)
            s = getattr(self.module, 'global_sustain', 0.8)
            r = getattr(self.module, 'global_release', 0.2)
            self.module.set_adsr(a, d, s, r)

    def set_global_decay(self, val):
        try:
            d = float(val)
        except:
            d = 0.1
        if hasattr(self.module, 'set_adsr'):
            a = getattr(self.module, 'global_attack', 0.01)
            s = getattr(self.module, 'global_sustain', 0.8)
            r = getattr(self.module, 'global_release', 0.2)
            self.module.set_adsr(a, d, s, r)

    def set_global_sustain(self, val):
        try:
            s = float(val)
        except:
            s = 0.8
        if s < 0.0:
            s = 0.0
        if s > 1.0:
            s = 1.0
        if hasattr(self.module, 'set_adsr'):
            a = getattr(self.module, 'global_attack', 0.01)
            d = getattr(self.module, 'global_decay', 0.1)
            r = getattr(self.module, 'global_release', 0.2)
            self.module.set_adsr(a, d, s, r)

    def set_global_release(self, val):
        try:
            r = float(val)
        except:
            r = 0.2
        if hasattr(self.module, 'set_adsr'):
            a = getattr(self.module, 'global_attack', 0.01)
            d = getattr(self.module, 'global_decay', 0.1)
            s = getattr(self.module, 'global_sustain', 0.8)
            self.module.set_adsr(a, d, s, r)
