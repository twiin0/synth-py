# audio.py

import pyaudio
import numpy as np
from synthesizer.limiter import Limiter

class AudioManager:
    """
    A unified audio manager that:
      1) Maintains a single chain of modules (self.module_chain).
      2) Supports note on/off via keyboard.
      3) Exposes global volume & optional global param setters.
      4) Provides audio_callback that processes modules in order.
    """
    def __init__(self, sample_rate=44100, buffer_size=1024):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        
        # Single chain of modules (left-to-right in the staging area).
        self.module_chain = []

        # Global controls
        self.global_volume = 1.0
        self.global_gain = 1.0

        # Limiter at final stage
        self.limiter = Limiter(sample_rate=self.sample_rate, threshold=0.95)

        # PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.running = False
        self.stopped = False

        # Keyboard thread
        self.keyboard_listener = None

    # ─────────────────────────────────────────
    # 1. GLOBAL PARAMS
    # ─────────────────────────────────────────
    def set_global_volume(self, vol):
        """
        Simple global volume that scales final mix.
        """
        self.global_volume = vol

    def set_global_gain(self, gain):
        """
        Simple global volume that scales final mix.
        """
        self.global_gain = gain

    def set_global_waveform(self, waveform):
        """
        Example: if a module has set_waveform(...) we call it here.
        """
        for module in self.module_chain:
            if hasattr(module, 'set_waveform'):
                module.set_waveform(waveform)

    def set_global_frequency(self, freq):
        """
        Example: if a module has set_frequency(...) we call it here.
        """
        for module in self.module_chain:
            if hasattr(module, 'set_frequency'):
                module.set_frequency(freq)

    def set_global_attack(self, attack_time):
        """
        Example: if a module has set_adsr(...) we pass the new attack to it.
        """
        for module in self.module_chain:
            if hasattr(module, 'set_adsr'):
                # get the other ADSR times from the module and update only attack
                at, dc, su, re = (
                    getattr(module, 'global_attack', None),
                    getattr(module, 'global_decay', None),
                    getattr(module, 'global_sustain', None),
                    getattr(module, 'global_release', None)
                )
                # If the module indeed stores them, set new times
                if at is not None:
                    # use this pattern or the module might store them differently
                    module.set_adsr(attack_time, dc, su, re)

    # and similarly for decay, sustain, release, etc.
    # Or if you want to do this in one shot, 
    # you'd do set_adsr() with all 4.

    # ─────────────────────────────────────────
    # 2. KEYBOARD NOTE HANDLER
    # ─────────────────────────────────────────
    def note_handler(self, midi_note, is_press, source="user"):
        """
        If source="user", we check if there's an arpeggiator. If so, 
        send the event there; otherwise, send to the synth modules.
        If source="arpeggiator", we skip the arpeggiator and go 
        straight to the synth modules.
        """

        if source == "user":
            arpeggiator = None
            for module in self.module_chain:
                if module.__class__.__name__ == "ArpeggiatorModule":
                    arpeggiator = module
                    break

            if arpeggiator:
                if is_press:
                    arpeggiator.note_on(midi_note)
                else:
                    arpeggiator.note_off(midi_note)
            else:
                for module in self.module_chain:
                    if hasattr(module, 'note_on') and hasattr(module, 'note_off'):
                        if is_press:
                            module.note_on(midi_note)
                        else:
                            module.note_off(midi_note)

        elif source == "arpeggiator":
            for module in self.module_chain:
                if module.__class__.__name__ != "ArpeggiatorModule":
                    if hasattr(module, 'note_on') and hasattr(module, 'note_off'):
                        if is_press:
                            module.note_on(midi_note)
                        else:
                            module.note_off(midi_note)


    # ─────────────────────────────────────────
    # 3. AUDIO CALLBACK
    # ─────────────────────────────────────────
    def audio_callback(self, in_data, frame_count, time_info, status):
        """
        Streams audio by passing 'None' into the first module
        and chaining each module's output into the next.
        Then applies global volume & limiter at the end.
        """
        current_audio = None
        for module in self.module_chain:
            current_audio = module.generate(frame_count, current_audio)

        if current_audio is None:
            current_audio = np.zeros(frame_count, dtype=np.float32)

        # Global volume
        current_audio *= self.global_volume

        # Final limiter
        processed = self.limiter.process_block(current_audio)
        processed *= self.global_gain

        np.clip(processed, -1.0, 1.0, out=processed)
        
        # Convert to int16
        out_int16 = (processed * 32767).astype(np.int16)
        return (out_int16.tobytes(), pyaudio.paContinue)

    # ─────────────────────────────────────────
    # 4. START/STOP STREAM
    # ─────────────────────────────────────────
    def start_stream(self):
        """
        Initialize & start PyAudio stream, plus keyboard thread.
        """
        if self.stopped:
            # If previously stopped, re-init pyaudio if needed
            self.p = pyaudio.PyAudio()
            self.stopped = False

        if self.stream is None:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.buffer_size,
                stream_callback=self.audio_callback
            )

        self.stream.start_stream()
        self.running = True
        print("Audio stream started. Press keys to play notes...")

    def stop_stream(self):
        """
        Gracefully stop the stream (public method you can call).
        """
        if not self.running:
            return
        self.running = False
        self.stopped = True

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        print("Audio stream stopped.")

    def stop(self):
        """
        Called internally by _keyboard_loop() or other places to stop everything.
        """
        self.stop_stream()
