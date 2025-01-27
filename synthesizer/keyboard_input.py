from pynput import keyboard

class KeyboardInput:
    def __init__(self, note_callback, audio_manager):
        self.note_callback = note_callback
        self.audio_manager = audio_manager
        self.key_to_note = {
            'a': 60,  # C4
            'w': 61,  # C#4
            's': 62,  # D4
            'e': 63,  # D#4
            'd': 64,  # E4
            'f': 65,  # F4
            't': 66,  # F#4
            'g': 67,  # G4
            'y': 68,  # G#4
            'h': 69,  # A4
            'u': 70,  # A#4
            'j': 71,  # B4
            'k': 72,  # C5
        }
        self.pressed_keys = set()
        self.listener = None

    def handle_key(self, key, is_press):
        """Unified key handler for press and release events."""
        if hasattr(key, 'char') and key.char:
            key_char = key.char.lower()
            if key_char in self.key_to_note:
                note = self.key_to_note[key_char]
                if is_press and key_char not in self.pressed_keys:
                    self.note_callback(note, True)  # Note-on
                    self.pressed_keys.add(key_char)
                elif not is_press and key_char in self.pressed_keys:
                    self.pressed_keys.remove(key_char)
                    self.note_callback(note, False)  # Note-off

        if key == keyboard.Key.esc and is_press:
            print("Escape key pressed. Exiting...")
            self.audio_manager.stop()  # Stop the audio playback
            if self.listener:
                self.listener.stop()  # Stop the listener explicitly

    def on_press(self, key):
        """Handle key press events."""
        self.handle_key(key, is_press=True)

    def on_release(self, key):
        """Handle key release events."""
        self.handle_key(key, is_press=False)

    def start(self):
        """Start listening to keyboard events."""
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()  # Start the listener
        self.listener.join()  # Block until the listener is stopped