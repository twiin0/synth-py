import numpy as np

class Module:
    """
    Base class for all synthesizer modules.
    Each module has a `generate(num_samples, input_audio=None)` method.
    """
    def generate(self, num_samples, input_audio=None):
        """
        Default behavior: if input_audio is given, pass it through unchanged;
        if no input is given, return silence.
        """
        if input_audio is None:
            return np.zeros(num_samples, dtype=np.float32)
        return input_audio
