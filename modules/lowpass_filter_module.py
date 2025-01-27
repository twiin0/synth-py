# modules/LowPassFilterModule.py

import numpy as np
from .module import Module

class LowPassFilterModule(Module):
    """
    A 1-pole low-pass filter module that processes input_audio.
    """
    def __init__(self, cutoff=1000.0, sample_rate=44100):
        self.cutoff = cutoff
        self.sample_rate = sample_rate
        self.z1 = 0.0
        self._update_alpha()

    def _update_alpha(self):
        # alpha = 1 - exp(-2*pi*cutoff/fs)
        self.alpha = 1.0 - np.exp(-2.0 * np.pi * self.cutoff / self.sample_rate)

    def set_cutoff(self, new_cutoff: float):
        """
        Called by ModuleFrame 'on_lpf_cutoff_change' 
        to update the filter's cutoff frequency.
        """
        self.cutoff = new_cutoff
        self._update_alpha()

    def generate(self, num_samples: int, input_audio=None):
        """
        Processes 'input_audio' with the 1-pole lowpass.
        If 'input_audio' is None, returns a block of zeros.
        """
        if input_audio is None:
            return np.zeros(num_samples, dtype=np.float32)

        out = np.zeros_like(input_audio)
        for i in range(num_samples):
            self.z1 = self.z1 + self.alpha * (input_audio[i] - self.z1)
            out[i] = self.z1
        return out
