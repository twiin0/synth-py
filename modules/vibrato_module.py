# modules/VibratoModule.py

import numpy as np
import math
from .module import Module

class VibratoModule(Module):
    """
    A vibrato effect by modulating a short delay line.
    'depth_ms' sets how many ms we modulate around base_delay_ms,
    'lfo_rate' sets the LFO speed in Hz.
    """
    def __init__(self, sample_rate=44100, base_delay_ms=10.0, depth_ms=1.0, lfo_rate=5.0, wave='sine'):
        self.sample_rate = sample_rate
        self.base_delay_ms = base_delay_ms
        self.depth_ms = depth_ms
        self.lfo_rate = lfo_rate
        self.wave = wave  # 'sine', 'square', 'triangle', 'sawtooth'
        
        # ring buffer for delay line processing
        self.ring_buffer_size = int(sample_rate * 2.0)  # 2-second buffer
        self.ring_buffer = np.zeros(self.ring_buffer_size, dtype=np.float32)
        self.write_ptr = 0
        self.phase = 0.0

    def set_depth_ms(self, new_depth_ms: float):
        """
        Called by 'on_vibrato_depth_change' to update vibrato depth in milliseconds.
        """
        self.depth_ms = max(0.0, new_depth_ms)

    def set_rate(self, new_rate: float):
        """
        Called by 'on_vibrato_freq_change' to update LFO rate in Hz.
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
        based on the current phase and selected waveform.
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
        Processes input audio by modulating a short delay line with vibrato.
        If input_audio is None, returns zeros.
        """
        if input_audio is None:
            return np.zeros(num_samples, dtype=np.float32)

        out = np.zeros(num_samples, dtype=input_audio.dtype)
        phase_inc = 2.0 * math.pi * self.lfo_rate / self.sample_rate

        base_delay_samples = self.base_delay_ms * 0.001 * self.sample_rate
        depth_samples = self.depth_ms * 0.001 * self.sample_rate

        for i in range(num_samples):
            # Write the current sample into the ring buffer.
            self.ring_buffer[self.write_ptr] = input_audio[i]

            # Calculate modulation value based on the chosen LFO wave.
            mod_value = self._lfo_value(self.phase)
            # Compute delay in samples (modulated around the base delay).
            delay = base_delay_samples + depth_samples * mod_value

            # Compute the read pointer for the delay line.
            read_ptr = self.write_ptr - delay
            read_ptr = (read_ptr + 2 * self.ring_buffer_size) % self.ring_buffer_size

            # Linear interpolation for smoother delay effect.
            r_floor = int(np.floor(read_ptr))
            r_ceil = (r_floor + 1) % self.ring_buffer_size
            frac = read_ptr - r_floor

            s_floor = self.ring_buffer[r_floor]
            s_ceil = self.ring_buffer[r_ceil]
            out[i] = (1.0 - frac) * s_floor + frac * s_ceil

            # Update the write pointer.
            self.write_ptr = (self.write_ptr + 1) % self.ring_buffer_size

            # Increment phase and keep it within 0 to 2π.
            self.phase += phase_inc
            if self.phase >= 2.0 * math.pi:
                self.phase -= 2.0 * math.pi

        return out
