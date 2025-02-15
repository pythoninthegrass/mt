import objc
import Quartz
import queue
import sys
from Foundation import NSObject

# NSEvent.h
NSSystemDefined = 14

# hidsystem/ev_keymap.h
NX_KEYTYPE_SOUND_UP = 0
NX_KEYTYPE_SOUND_DOWN = 1
NX_KEYTYPE_PLAY = 16
NX_KEYTYPE_NEXT = 17
NX_KEYTYPE_PREVIOUS = 18
NX_KEYTYPE_FAST = 19
NX_KEYTYPE_REWIND = 20

def HIDPostAuxKey(key):
    """Post a media key event to the system."""
    def doKey(down):
        ev = Quartz.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
            NSSystemDefined,  # type
            (0, 0),  # location
            0xa00 if down else 0xb00,  # flags
            0,  # timestamp
            0,  # window
            0,  # ctx
            8,  # subtype
            (key << 16) | ((0xa if down else 0xb) << 8),  # data1
            -1  # data2
        )
        cev = ev.CGEvent()
        Quartz.CGEventPost(0, cev)
    doKey(True)
    doKey(False)

class EventHandler(NSObject):
    """Event handler for media key events."""
    def initWithController_(self, controller):
        self = objc.super(EventHandler, self).init()
        if self is None:
            return None
        self.controller = controller
        return self

    def handleEvent_(self, event):
        """Handle media key events."""
        if event.type() == NSSystemDefined and event.subtype() == 8:
            data = event.data1()
            key_code = (data & 0xFFFF0000) >> 16
            key_state = (data & 0x0000FF00) >> 8
            if key_state == 0xA:  # Key pressed
                print(f"Media key pressed: {key_code}")  # Debug log
                self.controller.handle_media_key(key_code)
        return event

class MediaKeyController:
    """Controller for handling media key events."""
    def __init__(self, window):
        print("Initializing MediaKeyController")  # Debug log
        self.window = window
        self.player = None  # Will be set by MusicPlayer
        self.command_queue = queue.Queue()
        self.setup_media_keys()
        self.setup_command_processor()

    def setup_media_keys(self):
        """Setup media key event monitoring."""
        try:
            print("Setting up media key monitoring")  # Debug log
            # Create event handler
            self.event_handler = EventHandler.alloc().initWithController_(self)

            # Create event tap
            mask = Quartz.NSEventMaskSystemDefined
            self.event_monitor = Quartz.NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
                mask, self.event_handler.handleEvent_
            )
            print("Media key monitoring setup complete")  # Debug log
        except Exception as e:
            print(f"Error setting up media keys: {e}")

    def setup_command_processor(self):
        """Setup periodic command processing in the main thread."""
        self.process_commands()

    def process_commands(self):
        """Process any pending commands in the queue."""
        try:
            while True:  # Process all pending commands
                command = self.command_queue.get_nowait()
                if command == 'play_pause':
                    self.player.play_pause()
                elif command == 'next_song':
                    self.player.player_core.next_song()
                elif command == 'previous_song':
                    self.player.player_core.previous_song()
        except queue.Empty:
            pass  # No more commands to process
        finally:
            # Schedule the next check
            self.window.after(100, self.process_commands)

    def set_player(self, player):
        """Set the player instance for direct function calls."""
        print("Setting player instance in MediaKeyController")  # Debug log
        self.player = player

    def handle_media_key(self, key_code):
        """Handle media key press by queueing commands for the main thread."""
        if not self.player:
            print("Player not set, cannot handle media keys")
            return

        try:
            print(f"Handling media key: {key_code}")  # Debug log
            if key_code == NX_KEYTYPE_PLAY:  # Play/Pause (F8)
                print("Queueing play_pause command")  # Debug log
                self.command_queue.put('play_pause')
            elif key_code == NX_KEYTYPE_FAST:  # Next Track (F9)
                print("Queueing next_song command")  # Debug log
                self.command_queue.put('next_song')
            elif key_code == NX_KEYTYPE_REWIND:  # Previous Track (F7)
                print("Queueing previous_song command")  # Debug log
                self.command_queue.put('previous_song')
        except Exception as e:
            print(f"Error handling media key: {e}")
            import traceback
            traceback.print_exc()  # Print full stack trace for debugging

    def post_media_key(self, command):
        """Post a media key event to the system."""
        key_map = {
            'playpause': NX_KEYTYPE_PLAY,
            'next': NX_KEYTYPE_NEXT,
            'prev': NX_KEYTYPE_PREVIOUS,
            'volup': NX_KEYTYPE_SOUND_UP,
            'voldown': NX_KEYTYPE_SOUND_DOWN
        }

        if command in key_map:
            HIDPostAuxKey(key_map[command])

    def __del__(self):
        """Clean up event monitor."""
        if hasattr(self, 'event_monitor') and self.event_monitor is not None:
            Quartz.NSEvent.removeMonitor_(self.event_monitor)
