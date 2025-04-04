import customtkinter
import tkinter as tk

from .collapsible_section import CollapsibleSection
from .module_frame import ModuleFrame

class SynthGUI(customtkinter.CTk):
    def __init__(self, audio_manager):
        super().__init__()
        self.audio_manager = audio_manager
        self.title("Twin's Synthesizer")
        self.geometry("1200x700")
        self.configure(fg_color="#252525")

        # Grid configuration
        self.grid_columnconfigure(0, weight=0)  # sidebar
        self.grid_columnconfigure(1, weight=1)  # center
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # Sidebar
        self.sidebar_frame = customtkinter.CTkFrame(
            self, 
            width=200, 
            fg_color="#1b1b1b"
        )
        self.sidebar_frame.grid(row=0, column=0, rowspan=3, sticky="nsw")

        # Oscillators section
        self.osc_section = CollapsibleSection(
            self.sidebar_frame,
            title="Oscillators",
            items=["Sine", "Triangle", "Sawtooth", "Square"],
            on_select=self.on_module_select
        )
        self.osc_section.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Filters section
        self.filter_section = CollapsibleSection(
            self.sidebar_frame,
            title="Filters",
            items=["Low-Pass Filter", "High-Pass Filter", "Band-Pass Filter"],
            on_select=self.on_module_select
        )
        self.filter_section.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # Effects section
        self.effects_section = CollapsibleSection(
            self.sidebar_frame,
            title="Effects",
            items=["Tremolo", "Vibrato"],
            on_select=self.on_module_select
        )
        self.effects_section.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        # Arpeggiators section (using a unique variable and grid row)
        self.arpeggiator_section = CollapsibleSection(
            self.sidebar_frame,
            title="Arpeggiators",
            items=["Arpeggiator"],
            on_select=self.on_module_select
        )
        self.arpeggiator_section.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

        # Top bar
        self.top_bar_frame = customtkinter.CTkFrame(
            self, 
            fg_color="#383838"
        )
        self.top_bar_frame.grid(row=0, column=1, sticky="new")
        self.top_bar_frame.grid_columnconfigure(0, weight=1)
        self.top_bar_frame.grid_columnconfigure(1, weight=0)
        self.top_bar_frame.grid_columnconfigure(2, weight=0)
        self.top_bar_frame.grid_columnconfigure(3, weight=0)
        self.top_bar_frame.grid_rowconfigure(0, weight=0)

        # Volume
        self.volume_label = customtkinter.CTkLabel(
            self.top_bar_frame, 
            text="Volume", 
            text_color="white"
        )
        self.volume_label.grid(row=0, column=0, sticky="w", padx=(10,0), pady=5)

        self.volume_var = tk.DoubleVar(value=1.0)
        self.volume_slider = customtkinter.CTkSlider(
            self.top_bar_frame, from_=0.0, to=1.0,
            variable=self.volume_var,
            command=self.on_volume_change, width=200
        )
        self.volume_slider.grid(row=0, column=0, sticky="w", padx=(70,5), pady=5)

        self.volume_entry_var = tk.StringVar(value="1.0")
        self.volume_entry = customtkinter.CTkEntry(
            self.top_bar_frame, 
            textvariable=self.volume_entry_var, 
            width=40
        )
        self.volume_entry.grid(row=0, column=0, sticky="w", padx=(280,0), pady=5)

        # Gain
        self.gain_label = customtkinter.CTkLabel(
            self.top_bar_frame,
            text="Gain", 
            text_color="white"
        )
        self.gain_label.grid(row=0, column=1, sticky="w", padx=(30,0), pady=5)

        self.gain_var = tk.DoubleVar(value=1.0)
        self.gain_slider = customtkinter.CTkSlider(
            self.top_bar_frame, from_=0.0, to=10,
            variable=self.gain_var,
            command=self.on_gain_change, width=200
        )
        self.gain_slider.grid(row=0, column=1, sticky="w", padx=(70,5), pady=5)

        self.gain_entry_var = tk.StringVar(value="1.0")
        self.gain_entry = customtkinter.CTkEntry(
            self.top_bar_frame, textvariable=self.gain_entry_var, width=40
        )
        self.gain_entry.grid(row=0, column=1, sticky="w", padx=(280,0), pady=5)

        # Start/Stop buttons
        self.start_button = customtkinter.CTkButton(
            self.top_bar_frame, text="Start Synth",
            fg_color="#4CAF50", hover_color="#45a049",
            text_color="white", command=self.on_start_synth
        )
        self.start_button.grid(row=0, column=2, sticky="e", padx=(60,10), pady=5)

        self.stop_button = customtkinter.CTkButton(
            self.top_bar_frame, text="Stop Synth",
            fg_color="red", hover_color="#bb3333",
            text_color="white", command=self.on_stop_synth
        )
        self.stop_button.grid(row=0, column=3, sticky="e", padx=(10,10), pady=5)

        # Center frame (dark grey area)
        self.center_frame = customtkinter.CTkFrame(
            self, 
            fg_color="#505050"
        )
        self.center_frame.grid(row=1, column=1, sticky="nsew")

        # Bottom row: Staging Area
        self.bottom_frame = customtkinter.CTkFrame(
            self, 
            fg_color="#404040", 
            height=400
        )
        self.bottom_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.bottom_frame.grid_columnconfigure(0, weight=0)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_rowconfigure(0, weight=0)
        self.bottom_frame.grid_rowconfigure(1, weight=0)

        # Staging area label
        self.staging_title = customtkinter.CTkLabel(
            self.bottom_frame, 
            text="Staging Area", 
            text_color="white", 
            font=("Arial",14)
        )
        self.staging_title.grid(row=0, column=0, columnspan=2, pady=(5,0))

        # The container for modules
        self.staging_area = customtkinter.CTkFrame(
            self.bottom_frame, 
            fg_color="#303030"
        )
        self.staging_area.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        self.staging_modules = []

    def on_module_select(self, module_name):
        mod_frame = ModuleFrame(self, module_name, self.audio_manager)
        self.staging_modules.append(mod_frame)
        self.refresh_staging_layout()

    def refresh_staging_layout(self):
        for i, mod_frame in enumerate(self.staging_modules):
            mod_frame.grid(row=0, column=i, padx=5, pady=5)

    def remove_module(self, mod_frame):
        if mod_frame in self.staging_modules:
            self.staging_modules.remove(mod_frame)
        mod_frame.grid_forget()
        mod_frame.destroy()
        self.refresh_staging_layout()

    # Volume/Gain Callbacks
    def on_volume_change(self, value):
        val = float(value)
        self.volume_entry_var.set(f"{val:.2f}")
        # Pass volume to AudioManager
        if hasattr(self.audio_manager.global_controls, 'set_global_volume'):
            self.audio_manager.global_controls.set_global_volume(val)

    def on_gain_change(self, value):
        val = float(value)
        self.gain_entry_var.set(f"{val:.2f}")
        # Pass gain to AudioManager
        if hasattr(self.audio_manager.global_controls, 'set_global_gain'):
            self.audio_manager.global_controls.set_global_gain(val)

    def on_start_synth(self):
        self.audio_manager.start_stream()

    def on_stop_synth(self):
        self.audio_manager.stop_stream()
