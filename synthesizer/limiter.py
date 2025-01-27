import numpy as np

class Limiter:
    def __init__(self, sample_rate, threshold=1.0, attack_time=0.01, release_time=0.01):
        """
        sample_rate:   The audio sample rate (e.g. 44100).
        threshold:     The maximum absolute amplitude we want (e.g., 1.0 for -1..+1 range).
        attack_time:   How quickly the limiter reduces gain if we exceed threshold (seconds).
        release_time:  How quickly the limiter restores gain if we are below threshold (seconds).
        """
        self.sample_rate = sample_rate
        self.threshold = threshold
        
        # Convert times to "coefficients" for exponential smoothing:
        # The shorter the time, the bigger (1 - exp(-1/(sr*time))) is, so gain changes faster.
        self.attack_coef  = np.exp(-1.0 / (sample_rate * attack_time))
        self.release_coef = np.exp(-1.0 / (sample_rate * release_time))
        
        # current_gain tracks how much attenuation or boost is currently being applied.
        self.current_gain = 1.0

    def process_block(self, audio_block):
        """
        Apply limiter to a block of audio samples (NumPy array).
        Returns a new array with the limiter gain applied.
        """
        # 1) Measure peak of the block
        block_peak = np.max(np.abs(audio_block))
        
        # 2) Determine the desired gain for this block
        if block_peak > self.threshold and block_peak > 0:
            desired_gain = self.threshold / block_peak
        else:
            desired_gain = 1.0  # No need to attenuate
        
        # 3) Smoothly transition to the desired gain
        if desired_gain < self.current_gain:
            # If we need to turn down, we use the attack time (fast change).
            self.current_gain += (desired_gain - self.current_gain) * (1.0 - self.attack_coef)
        else:
            # If we can turn up, we use the release time (slower change).
            self.current_gain += (desired_gain - self.current_gain) * (1.0 - self.release_coef)

        # 4) Apply the current gain
        return audio_block * self.current_gain