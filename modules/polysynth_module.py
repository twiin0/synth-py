# modules/PolySynthModule.py

import numpy as np
import math

class Voice:
    """
    Each voice has an oscillator + envelope, 
    using the PolySynth's global ADSR times. 
    """
    def __init__(self, sample_rate=44100, waveform='sine'):
        self.sample_rate = sample_rate
        self.waveform = waveform.lower()
        self.frequency = 440.0
        self.phase = 0.0
        self.active = False

        # Envelope state
        self.env_state = 'off'
        self.env_amplitude = 0.0
        self.env_step = 0.0
        # Local copies of the ADSR times
        self.attack = 0.01
        self.decay = 0.1
        self.sustain = 0.8
        self.release = 0.2

    def note_on(self, freq, attack, decay, sustain, release):
        self.frequency = freq
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release

        self.active = True
        self.env_state = 'attack'
        if self.attack <= 0:
            self.env_amplitude = 1.0
            self.env_state = 'decay'
        else:
            self.env_step = 1.0 / (self.sample_rate * self.attack)

    def note_off(self):
        if self.env_state != 'off':
            self.env_state = 'release'
            if self.release <= 0:
                self.env_amplitude = 0.0
                self.env_state = 'off'
                self.active = False
            else:
                self.env_step = -self.env_amplitude / (self.sample_rate * self.release)

    def generate_voice(self, num_samples):
        out = np.zeros(num_samples, dtype=np.float32)
        if not self.active:
            return out

        phase_inc = (2.0 * math.pi * self.frequency) / self.sample_rate
        for i in range(num_samples):
            # Envelope
            if self.env_state == 'attack':
                self.env_amplitude += self.env_step
                if self.env_amplitude >= 1.0:
                    self.env_amplitude = 1.0
                    self.env_state = 'decay'
                    diff = (1.0 - self.sustain)
                    if self.decay <= 0:
                        self.env_amplitude = self.sustain
                        self.env_state = 'sustain'
                    else:
                        self.env_step = diff / (self.sample_rate * self.decay)

            elif self.env_state == 'decay':
                self.env_amplitude -= self.env_step
                if self.env_amplitude <= self.sustain:
                    self.env_amplitude = self.sustain
                    self.env_state = 'sustain'

            elif self.env_state == 'sustain':
                self.env_amplitude = self.sustain

            elif self.env_state == 'release':
                self.env_amplitude += self.env_step
                if self.env_amplitude <= 0.0:
                    self.env_amplitude = 0.0
                    self.env_state = 'off'
                    self.active = False
                    break

            # Oscillator
            sample_val = 0.0
            if self.waveform == 'sine':
                sample_val = math.sin(self.phase)
            elif self.waveform == 'square':
                sample_val = 1.0 if math.sin(self.phase) >= 0 else -1.0
            elif self.waveform == 'triangle':
                sample_val = (2.0/math.pi) * math.asin(math.sin(self.phase))
            elif self.waveform == 'sawtooth':
                frac = (self.phase / (2*math.pi))
                sample_val = 2.0*frac - 1.0

            out[i] = sample_val * self.env_amplitude

            self.phase += phase_inc
            if self.phase >= 2.0 * math.pi:
                self.phase -= 2.0 * math.pi

        return out

class PolySynthModule:
    """
    A single module that manages multiple voices = oscillator + ADSR each.
    The ADSR is encapsulated (no separate ADSRModule).
    Now supports a 'base_freq' for transposing all notes.
    """
    def __init__(self, sample_rate=44100, max_voices=8, waveform='sine'):
        self.sample_rate = sample_rate
        self.max_voices = max_voices
        self.waveform = waveform.lower()

        # Our global ADSR times
        self.global_attack = 0.01
        self.global_decay = 0.1
        self.global_sustain = 0.8
        self.global_release = 0.2

        # base_freq is the reference for note 69 (A4). Default 440 Hz.
        self.base_freq = 440.0  

        # dict note -> Voice
        self.active_voices = {}

    def set_waveform(self, wf):
        self.waveform = wf.lower()
        # Optionally, update existing voices' waveforms if needed
        for v in self.active_voices.values():
            v.waveform = self.waveform

    def set_frequency(self, freq):
        """
        Interpreted as the new 'base_freq' for A4. 
        Shift all currently active voices proportionally.
        """
        if freq <= 0:
            return
        ratio = freq / self.base_freq
        self.base_freq = freq
        # Shift all active voices
        for v in self.active_voices.values():
            v.frequency *= ratio

    def set_adsr(self, attack, decay, sustain, release):
        """
        Called by the UI to set new ADSR times.
        New notes use these times, existing voices optionally updated.
        """
        self.global_attack = attack
        self.global_decay = decay
        self.global_sustain = sustain
        self.global_release = release

        # Update existing voices if they're still active
        for v in self.active_voices.values():
            if v.active:
                v.attack = attack
                v.decay = decay
                v.sustain = sustain
                v.release = release

    def note_on(self, note_number):
        """
        Convert MIDI note -> frequency, find or create a voice, start it w/ global ADSR times.
        freq = base_freq * 2^((note_number-69)/12)
        """
        freq = self.base_freq * (2.0**((note_number - 69)/12.0))
        if note_number in self.active_voices:
            v = self.active_voices[note_number]
            v.note_on(freq, self.global_attack, self.global_decay, self.global_sustain, self.global_release)
            return

        if len(self.active_voices) < self.max_voices:
            voice = Voice(sample_rate=self.sample_rate, waveform=self.waveform)
            voice.note_on(freq, self.global_attack, self.global_decay, self.global_sustain, self.global_release)
            self.active_voices[note_number] = voice
        else:
            # voice stealing
            stolen_key = None
            for k, v in self.active_voices.items():
                if not v.active:
                    stolen_key = k
                    break
            if stolen_key is None:
                stolen_key = list(self.active_voices.keys())[0]

            stolen_v = self.active_voices.pop(stolen_key)
            stolen_v.waveform = self.waveform
            stolen_v.note_on(freq, self.global_attack, self.global_decay, self.global_sustain, self.global_release)
            self.active_voices[note_number] = stolen_v

    def note_off(self, note_number):
        if note_number in self.active_voices:
            self.active_voices[note_number].note_off()

    def generate(self, num_samples, input_audio):
        """
        Summation of all active voices + optional chain input.
        """
        if input_audio is None:
            mixed = np.zeros(num_samples, dtype=np.float32)
        else:
            mixed = np.copy(input_audio)

        current_voices = list(self.active_voices.items())

        to_remove = []
        for note, voice in current_voices:
            block = voice.generate_voice(num_samples)
            block *= 0.1
            mixed += block
            if not voice.active:
                to_remove.append(note)

        for dead_note in to_remove:
            del self.active_voices[dead_note]

        return mixed
