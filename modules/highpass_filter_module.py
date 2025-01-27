# modules/HighPassFilterModule.py

import numpy as np
from .module import Module

class HighPassFilterModule(Module):
    """
    1-pole high-pass filter module.
    """
    def __init__(self, cutoff=500.0, sample_rate=44100):
        self.cutoff = cutoff
        self.sample_rate = sample_rate
        self.z1 = 0.0
        self.last_input = 0.0
        self._update_alpha()

    def _update_alpha(self):
        # alpha = exp(-2*pi*cutoff/fs)
        self.alpha = np.exp(-2.0 * np.pi * self.cutoff / self.sample_rate)

    def set_cutoff(self, new_cutoff: float):
        """
        Called by ModuleFrame 'on_hpf_cutoff_change' 
        to update the filter's cutoff frequency.
        """
        self.cutoff = new_cutoff
        self._update_alpha()

    def generate(self, num_samples: int, input_audio=None):
        """
        Processes 'input_audio' with the 1-pole highpass.
        If 'input_audio' is None, returns a block of zeros.
        """
        if input_audio is None:
            return np.zeros(num_samples, dtype=np.float32)

        out = np.zeros_like(input_audio)
        for i in range(num_samples):
            # y[n] = alpha * (z1 + x[n] - x[n-1])
            hp = self.alpha * (self.z1 + input_audio[i] - self.last_input)
            out[i] = hp
            self.z1 = hp
            self.last_input = input_audio[i]
        return out
