import numpy as np
from .module import Module

class ArpeggiatorModule(Module):
    """
    A block-based arpeggiator Module supporting "up", "down", and "updown" modes.

    It triggers repeated note_on/note_off events for any notes that are physically 
    or latched held.

    The arpeggiator is clocked by the block size, i.e. each generate(...) call sees 
    how many samples have passed, and if enough time has elapsed to move to the 
    next note in the pattern, we do so.

    (Does NOT transform audio -- input_audio is returned unchanged)
    """

    def __init__(self, 
                 note_callback,    # Must be: (midi_note: int, is_press: bool, source="user") -> None
                 sample_rate=44100,
                 mode="up",        # "up", "down", or "updown"
                 rate=6.0,         # notes per second
                 hold=False):
        super().__init__()

        self.note_callback = note_callback  # typically audio_manager.note_handler
        self.sample_rate = sample_rate

        # "up", "down", or "updown"
        self.mode = mode.lower().strip()
        if self.mode not in ["up", "down", "up-down"]:
            self.mode = "up"

        self.rate = rate
        self.hold_enabled = hold

        # The sets for physically held or latched notes
        self.held_notes = set()
        self.latched_notes = set()

        # The index in the arpeggio pattern
        self.current_index = 0
        # For "updown", we need a direction: +1 going up, -1 going down
        self.updown_direction = +1

        self.last_note_playing = None

        # Time measure in samples: how many samples have accumulated since last step
        self.samples_since_step = 0
        # Samples to wait per note
        self.samples_per_note = int(self.sample_rate / max(0.0001, self.rate))

    # ─────────────────────────────────────────────────────────
    # 1) Public Setters (ModuleFrame can call them)
    # ─────────────────────────────────────────────────────────
    def set_rate(self, new_rate: float):
        """
        Control how many notes per second the arpeggio cycles through.
        """
        self.rate = max(0.01, new_rate)
        self.samples_per_note = int(self.sample_rate / self.rate)

    def set_mode(self, new_mode: str):
        """
        "up", "down", or "updown"
        """
        new_mode = new_mode.lower().strip()
        if new_mode in ["up", "down", "updown"]:
            self.mode = new_mode

    def set_hold(self, is_hold: bool):
        """
        If hold (latch) is enabled, physically released notes remain in latched_notes.
        If hold is disabled, latched notes are removed if not physically held.
        """
        self.hold_enabled = is_hold
        if not is_hold:
            # remove latched notes that are not physically held
            to_remove = [n for n in self.latched_notes if n not in self.held_notes]
            for note in to_remove:
                self.latched_notes.remove(note)

    # ─────────────────────────────────────────────────────────
    # 2) Note On/Off from the user
    # ─────────────────────────────────────────────────────────
    def note_on(self, midi_note: int):
        """
        Called when a key is pressed.
        
        When hold_enabled is False, a key press simply adds the note 
        to held_notes.
        
        When hold_enabled is True, a key press acts as a toggle:
        - If the note is not already held, add it.
        - If it is already held, remove it (i.e. release it).
        """
        if self.hold_enabled:
            # Toggle behavior: if note already held, remove it; else add it.
            if midi_note in self.held_notes:
                self.held_notes.remove(midi_note)
                if midi_note in self.latched_notes:
                    self.latched_notes.remove(midi_note)
            else:
                self.held_notes.add(midi_note)
                self.latched_notes.add(midi_note)
        else:
            # Normal behavior: just add the note.
            self.held_notes.add(midi_note)


    def note_off(self, midi_note: int):
        """
        Called when a key is released.
        
        When hold_enabled is False, releasing a key removes it from held_notes 
        (and from latched_notes).
        
        When hold_enabled is True, we ignore note_off events because the 
        toggling is entirely handled by note_on.
        """
        if not self.hold_enabled:
            if midi_note in self.held_notes:
                self.held_notes.remove(midi_note)
            if midi_note in self.latched_notes:
                self.latched_notes.remove(midi_note)

    def clear_latched(self):
        """
        Manually clear out latched notes (if user toggles hold off).
        """
        self.latched_notes.clear()

    # ─────────────────────────────────────────────────────────
    # 3) The arpeggio logic
    # ─────────────────────────────────────────────────────────
    def _get_active_notes(self):
        """
        Return a sorted list of notes to arpeggiate: 
         - latched_notes if hold_enabled,
         - otherwise physically held_notes.

        For "up" or "down", we do a simple reverse. 
        For "updown", we keep them sorted ascending and rely on self.updown_direction 
        to move current_index forward/backward.
        """
        if self.hold_enabled:
            active = sorted(self.latched_notes)
        else:
            active = sorted(self.held_notes)
        return active

    def _advance_arpeggio(self, active):
        """
        Step to the next note based on self.mode and self.updown_direction.
        Turn off the old note and turn on the new note via self.note_callback(..., source="arpeggiator").
        """
        n = len(active)
        if n == 0:
            if self.last_note_playing is not None:
                # Turn off last playing note if needed
                self.note_callback(self.last_note_playing, False, source="arpeggiator")
                self.last_note_playing = None
            return

        if self.mode in ["up", "down"]:
            # We'll treat them as strictly ascending or descending
            if self.mode == "down":
                active.reverse()

            # pick note at current_index
            note = active[self.current_index % n]

            # Turn off last note if different
            if self.last_note_playing is not None and self.last_note_playing != note:
                self.note_callback(self.last_note_playing, False, source="arpeggiator")

            # Turn on the new note
            if note != self.last_note_playing:
                self.note_callback(note, True, source="arpeggiator")
                self.last_note_playing = note

            self.current_index += 1

        elif self.mode == "updown":
            # Clamp current_index in case the active list size changed
            if self.current_index < 0:
                self.current_index = 0
            elif self.current_index >= n:
                self.current_index = n - 1

            # Choose the note at current_index
            note = active[self.current_index]

            # Turn off the previously playing note if it is different
            if self.last_note_playing is not None and self.last_note_playing != note:
                self.note_callback(self.last_note_playing, False, source="arpeggiator")

            # Turn on the new note if not already on
            if note != self.last_note_playing:
                self.note_callback(note, True, source="arpeggiator")
                self.last_note_playing = note

            # Bounce logic:
            # Force upward if at the beginning; force downward if at the end.
            if self.current_index == 0:
                self.updown_direction = 1
            elif self.current_index == n - 1:
                self.updown_direction = -1

            # Update the index for the next step.
            self.current_index += self.updown_direction


    # ─────────────────────────────────────────────────────────
    # 4) generate(...)
    #    We'll treat each call as passing `num_samples` time. 
    #    If enough samples have elapsed to step to the next note, do so.
    #    Pass input_audio through unchanged (this module doesn't generate audio).
    # ─────────────────────────────────────────────────────────
    def generate(self, num_samples: int, input_audio=None):
        if input_audio is None:
            output = np.zeros(num_samples, dtype=np.float32)
        else:
            output = input_audio.copy()

        # Accumulate time
        self.samples_since_step += num_samples

        # Get the active notes once per block
        active = self._get_active_notes()
        num_active = len(active)

        # How many steps can we move in this block?
        while self.samples_since_step >= self.samples_per_note:
            self.samples_since_step -= self.samples_per_note
            self._advance_arpeggio(active)

        # If no notes are active but we have a note playing, turn it off
        if len(num_active) == 0 and self.last_note_playing is not None:
            self.note_callback(self.last_note_playing, False, source="arpeggiator")
            self.last_note_playing = None

        # Return the input unmodified (arpeggiator doesn't affect the audio)
        return output
