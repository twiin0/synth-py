# modules/TremoloModule.py

import numpy as np
import math
from .module import Module

class TremoloModule(Module):
    """
    A simple tremolo effect.
    'depth' sets how strong the amplitude modulation is (range [0, 1]),
    'rate' sets the LFO speed in Hz.
    """
    def __init__(self, sample_rate=44100, depth=0.5, lfo_rate=5.0, wave='sine'):
        self.sample_rate = sample_rate
        self.depth = depth       # range [0..1]
        self.lfo_rate = lfo_rate
        self.phase = 0.0
        self.wave = wave.lower()  # LFO waveform: 'sine', 'square', 'triangle', or 'sawtooth'
        
    def set_depth(self, new_depth: float):
        """
        Called by ModuleFrame 'on_tremolo_depth_change'
        to update tremolo depth.
        """
        self.depth = max(0.0, min(1.0, new_depth))

    def set_rate(self, new_rate: float):
        """
        Called by ModuleFrame 'on_tremolo_freq_change'
        to update LFO rate in Hz.
        """
        self.lfo_rate = max(0.0, new_rate)
        
    def set_wave_type(self, wave_type: str):
        """
        Updates the LFO waveform type.
        """
        allowed_waves = ['sine', 'square', 'triangle', 'sawtooth']
        if wave_type.lower() in allowed_waves:
            self.wave = wave_type.lower()
        else:
            print(f"Unknown wave type {wave_type}; defaulting to sine.")
            self.wave = 'sine'
    
    def _lfo_value(self, phase: float) -> float:
        """
        Returns the LFO modulation value (in the range -1 to 1)
        based on the current phase and the selected waveform.
        """
        if self.wave == 'sine':
            return math.sin(phase)
        elif self.wave == 'square':
            return math.tanh(20 * math.sin(phase))
        elif self.wave == 'triangle':
            # Normalize the result of arcsine to get a triangle waveform in the range [-1, 1].
            return (2.0 / math.pi) * math.asin(math.sin(phase))
        elif self.wave == 'sawtooth':
            # Normalize phase t to the range [0, 1)
            t = (phase % (2 * math.pi)) / (2 * math.pi)
            return (2.0 / math.pi) * math.fsum(((-1)**(n+1) / n) * math.sin(2 * math.pi * n * t) for n in range(1, 21))
        else:
            # default to sine wave
            return math.sin(phase)

    def generate(self, num_samples: int, input_audio=None):
        """
        Processes the input audio by modulating amplitude with an LFO.
        If input_audio is None, returns zeros.
        The amplitude factor is computed in such a way that it varies around unity.
        """
        if input_audio is None:
            return np.zeros(num_samples, dtype=np.float32)

        out = np.zeros_like(input_audio)
        phase_inc = 2.0 * math.pi * self.lfo_rate / self.sample_rate

        for i in range(num_samples):
            # Get the current LFO value in range [-1, 1] using the selected waveform.
            lfo = self._lfo_value(self.phase)
            # Convert it to an amplitude modulation factor.
            # Here we create a modulation factor around 1.0.
            # For example, with depth=0.5, the amplitude ranges from 0.75 to 1.25.
            mod_factor = 1.0 - (self.depth * 0.5) + lfo * (self.depth * 0.5)
            out[i] = input_audio[i] * mod_factor

            # Increment phase and wrap around at 2π.
            self.phase += phase_inc
            if self.phase >= 2 * math.pi:
                self.phase -= 2 * math.pi

        return out
