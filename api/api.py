import json
import socket
import threading
import traceback
from contextlib import suppress
from eliot import log_message, start_action
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from core.player import MusicPlayer

# Create API logger
try:
    from eliot import Logger

    api_logger = Logger()
except ImportError:
    api_logger = None


class APIServer:
    """Socket-based API server for controlling the mt music player."""

    def __init__(self, music_player: 'MusicPlayer', port: int = 5555):
        """Initialize the API server.

        Args:
            music_player: The MusicPlayer instance to control
            port: Port to listen on (default 5555)
        """
        self.music_player = music_player
        self.port = port
        self.server_socket: socket.socket | None = None
        self.server_thread: threading.Thread | None = None
        self.running = False

        # Command handlers mapping
        self.command_handlers = {
            # Playback controls
            'play_pause': self._handle_play_pause,
            'play': self._handle_play,
            'pause': self._handle_pause,
            'stop': self._handle_stop,
            'next': self._handle_next,
            'previous': self._handle_previous,
            # Track selection
            'select_track': self._handle_select_track,
            'play_track_at_index': self._handle_play_track_at_index,
            # Queue management
            'add_to_queue': self._handle_add_to_queue,
            'clear_queue': self._handle_clear_queue,
            'remove_from_queue': self._handle_remove_from_queue,
            # UI navigation
            'switch_view': self._handle_switch_view,
            'select_library_item': self._handle_select_library_item,
            'select_queue_item': self._handle_select_queue_item,
            # Slider controls
            'set_volume': self._handle_set_volume,
            'seek': self._handle_seek,
            'seek_to_position': self._handle_seek_to_position,
            # Utility controls
            'toggle_loop': self._handle_toggle_loop,
            'toggle_shuffle': self._handle_toggle_shuffle,
            'toggle_favorite': self._handle_toggle_favorite,
            # Media key simulation
            'media_key': self._handle_media_key,
            # Search
            'search': self._handle_search,
            'clear_search': self._handle_clear_search,
            # Info queries
            'get_status': self._handle_get_status,
            'get_current_track': self._handle_get_current_track,
            'get_queue': self._handle_get_queue,
            'get_library': self._handle_get_library,
        }

    def start(self):
        """Start the API server in a background thread."""
        if self.running:
            return {'status': 'error', 'message': 'Server already running'}

        with start_action(api_logger, "start_api_server", port=self.port):
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind(('localhost', self.port))
                self.server_socket.listen(5)

                self.running = True
                self.server_thread = threading.Thread(target=self._handle_clients, daemon=True, name="APIServerThread")
                self.server_thread.start()

                log_message(message_type="api_server_started", port=self.port)
                return {'status': 'success', 'message': f'API server started on port {self.port}'}

            except Exception as e:
                log_message(message_type="api_server_start_failed", error=str(e))
                return {'status': 'error', 'message': f'Failed to start server: {str(e)}'}

    def stop(self):
        """Stop the API server."""
        if not self.running:
            return {'status': 'error', 'message': 'Server not running'}

        with start_action(api_logger, "stop_api_server"):
            self.running = False

            # Close the server socket
            if self.server_socket:
                with suppress(Exception):
                    self.server_socket.close()
                self.server_socket = None

            # Wait for thread to finish
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=2)

            log_message(message_type="api_server_stopped")
            return {'status': 'success', 'message': 'API server stopped'}

    def _handle_clients(self):
        """Handle incoming client connections."""
        while self.running:
            try:
                # Set timeout so we can check running flag periodically
                self.server_socket.settimeout(1.0)

                try:
                    client_socket, address = self.server_socket.accept()
                except TimeoutError:
                    continue

                # Handle client in a separate thread
                client_thread = threading.Thread(target=self._handle_client_request, args=(client_socket, address), daemon=True)
                client_thread.start()

            except Exception as e:
                if self.running:  # Only log if we're still supposed to be running
                    log_message(message_type="client_accept_error", error=str(e))

    def _handle_client_request(self, client_socket: socket.socket, address):
        """Handle a single client request.

        Args:
            client_socket: The client's socket connection
            address: The client's address
        """
        try:
            # Receive data (max 4KB)
            data = client_socket.recv(4096).decode('utf-8')

            if not data:
                client_socket.close()
                return

            # Parse JSON command
            try:
                command = json.loads(data)
            except json.JSONDecodeError as e:
                response = {'status': 'error', 'message': f'Invalid JSON: {str(e)}'}
                client_socket.send(json.dumps(response).encode('utf-8'))
                client_socket.close()
                return

            # Log the received command
            with start_action(api_logger, "handle_api_command", action=command.get('action', 'unknown'), address=str(address)):
                # Execute command on main thread
                response = self._execute_command(command)

                # Send response
                client_socket.send(json.dumps(response).encode('utf-8'))

        except Exception as e:
            log_message(message_type="client_request_error", error=str(e))
            error_response = {'status': 'error', 'message': str(e)}
            with suppress(Exception):
                client_socket.send(json.dumps(error_response).encode('utf-8'))

        finally:
            with suppress(Exception):
                client_socket.close()

    def _execute_command(self, command: dict[str, Any]) -> dict[str, Any]:
        """Execute a command and return the response.

        Args:
            command: The command dictionary with 'action' and optional parameters

        Returns:
            Response dictionary with 'status' and optional data
        """
        action = command.get('action')

        if not action:
            return {'status': 'error', 'message': 'No action specified'}

        handler = self.command_handlers.get(action)

        if not handler:
            return {
                'status': 'error',
                'message': f'Unknown action: {action}',
                'available_actions': list(self.command_handlers.keys()),
            }

        try:
            # Execute handler on main thread using after() for thread safety
            result = {'status': 'pending'}
            event = threading.Event()

            def execute_on_main_thread():
                try:
                    result.update(handler(command))
                except Exception as e:
                    result.update({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()})
                finally:
                    event.set()

            # Schedule execution on main thread
            self.music_player.window.after(0, execute_on_main_thread)

            # Wait for execution to complete (with timeout)
            if event.wait(timeout=5):
                return result
            else:
                return {'status': 'error', 'message': 'Command execution timed out'}

        except Exception as e:
            return {'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}

    # === Playback Control Handlers ===

    def _handle_play_pause(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle play/pause toggle command."""
        self.music_player.play_pause()
        is_playing = self.music_player.player_core.is_playing
        return {'status': 'success', 'is_playing': is_playing}

    def _handle_play(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle play command."""
        if not self.music_player.player_core.is_playing:
            self.music_player.play_pause()
        return {'status': 'success', 'is_playing': True}

    def _handle_pause(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle pause command."""
        if self.music_player.player_core.is_playing:
            self.music_player.play_pause()
        return {'status': 'success', 'is_playing': False}

    def _handle_stop(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle stop command."""
        self.music_player.player_core.stop()
        return {'status': 'success'}

    def _handle_next(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle next track command."""
        self.music_player.player_core.next_song()
        return {'status': 'success'}

    def _handle_previous(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle previous track command."""
        self.music_player.player_core.previous_song()
        return {'status': 'success'}

    # === Track Selection Handlers ===

    def _handle_select_track(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle track selection by filepath."""
        filepath = command.get('filepath')
        if not filepath:
            return {'status': 'error', 'message': 'No filepath specified'}

        # Find and select the track
        success = self.music_player.player_core._select_item_by_filepath(filepath)
        if success:
            return {'status': 'success'}
        else:
            return {'status': 'error', 'message': 'Track not found in queue'}

    def _handle_play_track_at_index(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle playing track at specific queue index."""
        index = command.get('index')
        if index is None:
            return {'status': 'error', 'message': 'No index specified'}

        try:
            # Get queue items from database (source of truth)
            queue_items = self.music_player.queue_manager.get_queue_items()

            # Validate index against database queue
            if not (0 <= index < len(queue_items)):
                return {'status': 'error', 'message': f'Index {index} out of range'}

            # Get filepath from database queue at specified index
            filepath = queue_items[index][0]  # First element is filepath

            # Play the file directly
            self.music_player.player_core._play_file(filepath)

            # Update play button state
            self.music_player.progress_bar.controls.update_play_button(True)

            # Update favorite button
            is_favorite = self.music_player.favorites_manager.is_favorite(filepath)
            self.music_player.progress_bar.controls.update_favorite_button(is_favorite)

            # Set playback context to indicate we're playing from queue
            self.music_player.playback_context = 'now_playing'

            return {'status': 'success'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    # === Queue Management Handlers ===

    def _handle_add_to_queue(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle adding files to queue."""
        files = command.get('files', [])
        if not files:
            return {'status': 'error', 'message': 'No files specified'}

        added_count = 0
        for filepath in files:
            try:
                # Add to queue through queue manager
                self.music_player.queue_manager.add_to_queue(filepath)
                added_count += 1
            except Exception as e:
                log_message(message_type="add_to_queue_error", filepath=filepath, error=str(e))

        # Set playback context to use the queue table
        self.music_player.playback_context = None
        # Reload queue view to show the added tracks
        self.music_player.load_queue()

        return {'status': 'success', 'added': added_count}

    def _handle_clear_queue(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle clearing the queue."""
        # Stop playback and clear media to ensure clean state
        self.music_player.player_core.stop(reason="queue_cleared")
        self.music_player.queue_manager.clear_queue()
        self.music_player.load_queue()  # Refresh the queue view
        return {'status': 'success'}

    def _handle_remove_from_queue(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle removing track from queue."""
        index = command.get('index')
        if index is None:
            return {'status': 'error', 'message': 'No index specified'}

        try:
            queue_items = list(self.music_player.queue_manager.get_queue_items())
            if 0 <= index < len(queue_items):
                # Get track metadata from the queue item
                # get_queue_items returns: (filepath, artist, title, album, track_number, date)
                filepath, artist, title, album, track_num, date = queue_items[index][:6]
                self.music_player.queue_manager.remove_from_queue(title, artist, album, track_num)
                self.music_player.load_queue()  # Refresh the queue view
                return {'status': 'success'}
            else:
                return {'status': 'error', 'message': f'Index {index} out of range'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    # === UI Navigation Handlers ===

    def _handle_switch_view(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle switching between library sections."""
        view = command.get('view')
        if not view:
            return {'status': 'error', 'message': 'No view specified'}

        # Map view names to section names
        view_mapping = {
            'library': 'Library',
            'queue': 'Queue',
            'liked': 'Liked Songs',
            'top25': 'Top 25 Most Played',
        }

        section = view_mapping.get(view.lower())
        if not section:
            return {'status': 'error', 'message': f'Unknown view: {view}', 'available_views': list(view_mapping.keys())}

        # Simulate section selection
        self.music_player.on_section_select(section)
        return {'status': 'success', 'view': section}

    def _handle_select_library_item(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle selecting item in library view."""
        index = command.get('index')
        if index is None:
            return {'status': 'error', 'message': 'No index specified'}

        try:
            items = self.music_player.queue_view.queue.get_children()
            if 0 <= index < len(items):
                item = items[index]
                self.music_player.queue_view.queue.selection_set(item)
                self.music_player.queue_view.queue.focus(item)
                return {'status': 'success'}
            else:
                return {'status': 'error', 'message': f'Index {index} out of range'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _handle_select_queue_item(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle selecting item in queue view."""
        index = command.get('index')
        if index is None:
            return {'status': 'error', 'message': 'No index specified'}

        try:
            # Get queue items from database (source of truth)
            queue_items = self.music_player.queue_manager.get_queue_items()

            # Validate index against database queue
            if not (0 <= index < len(queue_items)):
                return {'status': 'error', 'message': f'Index {index} out of range'}

            # Ensure we're showing the queue view
            self.music_player.load_queue()

            # Now get UI items and select the one at the validated index
            items = self.music_player.queue_view.queue.get_children()
            if 0 <= index < len(items):
                item = items[index]
                self.music_player.queue_view.queue.selection_set(item)
                self.music_player.queue_view.queue.focus(item)
                return {'status': 'success'}
            else:
                # This shouldn't happen if database and UI are in sync
                return {'status': 'error', 'message': f'UI index {index} out of range'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    # === Slider Control Handlers ===

    def _handle_set_volume(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle volume setting command."""
        volume = command.get('volume')
        if volume is None:
            return {'status': 'error', 'message': 'No volume specified'}

        try:
            volume = float(volume)
            if not 0 <= volume <= 100:
                return {'status': 'error', 'message': 'Volume must be between 0 and 100'}

            self.music_player.player_core.set_volume(int(volume))
            return {'status': 'success', 'volume': volume}
        except (ValueError, TypeError) as e:
            return {'status': 'error', 'message': f'Invalid volume value: {str(e)}'}

    def _handle_seek(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle relative seek command."""
        offset = command.get('offset', 0)
        try:
            offset = float(offset)
            # Get current time in milliseconds and convert to seconds
            current_time_ms = self.music_player.player_core.get_current_time()
            current_time_sec = current_time_ms / 1000.0
            # Calculate new position in seconds
            new_time_sec = current_time_sec + offset
            # Use seek_to_time with verification
            success = self.music_player.player_core.seek_to_time(new_time_sec, source="api")
            if success:
                return {'status': 'success', 'new_position': new_time_sec}
            else:
                return {'status': 'error', 'message': 'Seek verification timeout'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _handle_seek_to_position(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle absolute seek command (position in seconds)."""
        position = command.get('position')
        if position is None:
            return {'status': 'error', 'message': 'No position specified'}

        try:
            position = float(position)
            # Use seek_to_time with verification and configurable timeout
            timeout = command.get('timeout', 2.0)
            success = self.music_player.player_core.seek_to_time(
                position,
                source="api",
                timeout=timeout
            )
            if success:
                return {'status': 'success', 'position': position}
            else:
                return {'status': 'error', 'message': 'Seek verification timeout'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    # === Utility Control Handlers ===

    def _handle_toggle_loop(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle loop toggle command."""
        self.music_player.player_core.toggle_loop()
        loop_enabled = self.music_player.player_core.loop_enabled
        return {'status': 'success', 'loop_enabled': loop_enabled}

    def _handle_toggle_shuffle(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle shuffle toggle command."""
        self.music_player.player_core.toggle_shuffle()
        shuffle_enabled = self.music_player.player_core.shuffle_enabled
        return {'status': 'success', 'shuffle_enabled': shuffle_enabled}

    def _handle_toggle_favorite(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle favorite toggle command."""
        self.music_player.toggle_favorite()
        return {'status': 'success'}

    # === Media Key Simulation ===

    def _handle_media_key(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle media key simulation."""
        key = command.get('key')
        if not key:
            return {'status': 'error', 'message': 'No key specified'}

        valid_keys = ['play_pause', 'next', 'previous']
        if key not in valid_keys:
            return {'status': 'error', 'message': f'Invalid key: {key}', 'valid_keys': valid_keys}

        # Simulate media key press
        if key == 'play_pause':
            self.music_player.play_pause()
        elif key == 'next':
            self.music_player.player_core.next_song()
        elif key == 'previous':
            self.music_player.player_core.previous_song()

        return {'status': 'success', 'key': key}

    # === Search Handlers ===

    def _handle_search(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle search command."""
        query = command.get('query', '')
        self.music_player.search_bar.search_var.set(query)
        self.music_player.perform_search(query)
        return {'status': 'success', 'query': query}

    def _handle_clear_search(self, command: dict[str, Any]) -> dict[str, Any]:
        """Handle clear search command."""
        self.music_player.clear_search()
        return {'status': 'success'}

    # === Info Query Handlers ===

    def _handle_get_status(self, command: dict[str, Any]) -> dict[str, Any]:
        """Get current player status."""
        try:
            # Convert times from milliseconds to seconds for API consistency
            current_time_ms = self.music_player.player_core.get_current_time()
            duration_ms = self.music_player.player_core.get_duration()

            status = {
                'is_playing': self.music_player.player_core.is_playing,
                'loop_enabled': self.music_player.player_core.loop_enabled,
                'shuffle_enabled': self.music_player.player_core.shuffle_enabled,
                'volume': self.music_player.player_core.get_volume(),
                'current_time': current_time_ms / 1000.0 if current_time_ms > 0 else 0.0,
                'duration': duration_ms / 1000.0 if duration_ms > 0 else 0.0,
                'current_view': getattr(self.music_player, '_current_view', 'Unknown'),
            }

            # Get current track info
            current_track = self.music_player.player_core._get_current_track_info()
            if current_track:
                status['current_track'] = {
                    'title': current_track.get('title', 'Unknown'),
                    'artist': current_track.get('artist', 'Unknown'),
                    'album': current_track.get('album', 'Unknown'),
                    'filepath': current_track.get('filepath', ''),
                }

            return {'status': 'success', 'data': status}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _handle_get_current_track(self, command: dict[str, Any]) -> dict[str, Any]:
        """Get current track information."""
        try:
            track_info = self.music_player.player_core._get_current_track_info()
            if track_info and track_info.get('track') != 'none':
                # Add filepath from current_file if available
                if hasattr(self.music_player.player_core, 'current_file') and self.music_player.player_core.current_file:
                    track_info['filepath'] = self.music_player.player_core.current_file
                return {'status': 'success', 'data': track_info}
            else:
                return {'status': 'success', 'data': None, 'message': 'No track playing'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _handle_get_queue(self, command: dict[str, Any]) -> dict[str, Any]:
        """Get current queue from database."""
        try:
            # Query the database queue, not the UI widget (which shows current view)
            db_queue_items = self.music_player.queue_manager.get_queue_items()
            queue_items = []

            for item in db_queue_items:
                # item format: (filepath, artist, title, album, track_number, date)
                queue_items.append(
                    {
                        'index': len(queue_items),
                        'title': item[2] if len(item) > 2 else '',
                        'artist': item[1] if len(item) > 1 else '',
                        'album': item[3] if len(item) > 3 else '',
                    }
                )

            return {'status': 'success', 'data': queue_items, 'count': len(queue_items)}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _handle_get_library(self, command: dict[str, Any]) -> dict[str, Any]:
        """Get library contents (limited to first 100 items for performance)."""
        try:
            library_items = []
            # Library content is displayed in queue_view.queue after load_library() is called
            items = self.music_player.queue_view.queue.get_children()[:100]  # Limit to 100

            for item in items:
                values = self.music_player.queue_view.queue.item(item, 'values')
                library_items.append(
                    {
                        'index': len(library_items),
                        'track': values[0] if len(values) > 0 else '',
                        'title': values[1] if len(values) > 1 else '',
                        'artist': values[2] if len(values) > 2 else '',
                        'album': values[3] if len(values) > 3 else '',
                    }
                )

            return {
                'status': 'success',
                'data': library_items,
                'count': len(library_items),
                'total': len(self.music_player.queue_view.queue.get_children()),
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
