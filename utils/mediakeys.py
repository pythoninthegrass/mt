import objc
import Quartz
import queue
import sys
from core.logging import controls_logger, log_player_action
from eliot import start_action
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
            0xA00 if down else 0xB00,  # flags
            0,  # timestamp
            0,  # window
            0,  # ctx
            8,  # subtype
            (key << 16) | ((0xA if down else 0xB) << 8),  # data1
            -1,  # data2
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

                with start_action(controls_logger, "execute_media_key_command"):
                    if command == 'play_pause':
                        log_player_action("play_pause", trigger_source="media_key", command_executed=True)
                        self.player.play_pause()
                    elif command == 'next_song':
                        log_player_action("next_song", trigger_source="media_key", command_executed=True)
                        self.player.player_core.next_song()
                    elif command == 'previous_song':
                        log_player_action("previous_song", trigger_source="media_key", command_executed=True)
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

        # Map key codes to human-readable names and actions
        key_map = {
            NX_KEYTYPE_PLAY: ("play_pause", "play_pause"),
            NX_KEYTYPE_FAST: ("next", "next_song"),
            NX_KEYTYPE_REWIND: ("previous", "previous_song"),
        }

        if key_code not in key_map:
            print(f"Unknown media key code: {key_code}")
            return

        key_name, action = key_map[key_code]

        with start_action(controls_logger, "media_key_press"):
            try:
                log_player_action(
                    action,
                    trigger_source="media_key",
                    key_type=key_name,
                    key_code=key_code,
                    message=f"Media key pressed: {key_name}",
                )

                print(f"Queueing {action} command")  # Debug log
                self.command_queue.put(action)
            except Exception as e:
                print(f"Error handling media key: {e}")
                import traceback

                traceback.print_exc()  # Print full stack trace for debugging  # Print full stack trace for debugging

    def post_media_key(self, command):
        """Post a media key event to the system."""
        key_map = {
            'playpause': NX_KEYTYPE_PLAY,
            'next': NX_KEYTYPE_NEXT,
            'prev': NX_KEYTYPE_PREVIOUS,
            'volup': NX_KEYTYPE_SOUND_UP,
            'voldown': NX_KEYTYPE_SOUND_DOWN,
        }

        if command in key_map:
            HIDPostAuxKey(key_map[command])

    def __del__(self):
        """Clean up event monitor."""
        if hasattr(self, 'event_monitor') and self.event_monitor is not None:
            Quartz.NSEvent.removeMonitor_(self.event_monitor)
