"""Audio streaming service for HTTP range request support."""

import os
from pathlib import Path
from typing import Optional, Tuple, BinaryIO
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from eliot import log_message


class AudioStreamingService:
    """Service for streaming audio files with HTTP range request support."""

    # Supported audio formats and their MIME types
    SUPPORTED_FORMATS = {
        '.mp3': 'audio/mpeg',
        '.flac': 'audio/flac',
        '.m4a': 'audio/mp4',
        '.aac': 'audio/aac',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.wma': 'audio/x-ms-wma',
        '.aiff': 'audio/aiff',
        '.aif': 'audio/aiff',
    }

    def __init__(self):
        """Initialize the audio streaming service."""
        pass

    def is_supported_format(self, file_path: str) -> bool:
        """
        Check if the file format is supported for streaming.

        Args:
            file_path: Path to the audio file

        Returns:
            True if the format is supported
        """
        path = Path(file_path)
        return path.suffix.lower() in self.SUPPORTED_FORMATS

    def get_mime_type(self, file_path: str) -> str:
        """
        Get the MIME type for an audio file.

        Args:
            file_path: Path to the audio file

        Returns:
            MIME type string
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        return self.SUPPORTED_FORMATS.get(extension, 'application/octet-stream')

    def validate_file_access(self, file_path: str) -> Path:
        """
        Validate that a file exists and is accessible for streaming.

        Args:
            file_path: Path to the audio file

        Returns:
            Resolved Path object

        Raises:
            HTTPException: If file is not accessible
        """
        try:
            path = Path(file_path).resolve()

            # Security checks
            if not path.exists():
                raise HTTPException(status_code=404, detail="Audio file not found")

            if not path.is_file():
                raise HTTPException(status_code=400, detail="Path is not a file")

            if not os.access(path, os.R_OK):
                raise HTTPException(status_code=403, detail="File is not readable")

            # Check file size (prevent streaming extremely large files)
            file_size = path.stat().st_size
            if file_size > 500 * 1024 * 1024:  # 500MB limit
                raise HTTPException(status_code=413, detail="File too large for streaming")

            # Validate format
            if not self.is_supported_format(str(path)):
                raise HTTPException(status_code=415, detail="Unsupported audio format")

            return path

        except HTTPException:
            raise
        except Exception as e:
            log_message(message_type="file_validation_error", file_path=file_path, error=str(e), error_type=type(e).__name__)
            raise HTTPException(status_code=500, detail="File validation failed")

    def parse_range_header(self, range_header: Optional[str], file_size: int) -> Tuple[int, int]:
        """
        Parse HTTP Range header and return byte range.

        Args:
            range_header: Range header value (e.g., "bytes=0-1023")
            file_size: Total file size in bytes

        Returns:
            Tuple of (start_byte, end_byte) inclusive

        Raises:
            HTTPException: If range is invalid
        """
        if not range_header or not range_header.startswith('bytes='):
            # No range specified, return entire file
            return 0, file_size - 1

        range_spec = range_header[6:]  # Remove 'bytes=' prefix

        try:
            if '-' not in range_spec:
                raise ValueError("Invalid range format")

            start_str, end_str = range_spec.split('-', 1)

            if start_str:
                start_byte = int(start_str)
            else:
                start_byte = 0

            if end_str:
                end_byte = int(end_str)
            else:
                end_byte = file_size - 1

            # Validate range
            if start_byte < 0 or end_byte >= file_size or start_byte > end_byte:
                raise HTTPException(status_code=416, detail=f"Range not satisfiable. File size: {file_size}")

            return start_byte, end_byte

        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid range header: {e}")

    def create_streaming_response(
        self, file_path: str, range_header: Optional[str] = None, chunk_size: int = 8192
    ) -> StreamingResponse:
        """
        Create a streaming response for an audio file with range support and concurrent request optimizations.

        Features:
        - HTTP range request support for partial content streaming
        - Efficient chunked streaming to handle concurrent requests
        - Proper caching headers for browser optimization
        - Connection keep-alive for multiple requests
        - Memory-efficient file reading

        Args:
            file_path: Path to the audio file
            range_header: HTTP Range header value
            chunk_size: Size of chunks to stream (default: 8192 bytes)

        Returns:
            FastAPI StreamingResponse optimized for concurrent access
        """
        # Validate file access
        path = self.validate_file_access(file_path)
        file_size = path.stat().st_size
        mime_type = self.get_mime_type(str(path))

        # Parse range
        start_byte, end_byte = self.parse_range_header(range_header, file_size)
        content_length = end_byte - start_byte + 1

        log_message(
            message_type="audio_stream_start",
            file_path=str(path),
            file_size=file_size,
            range_start=start_byte,
            range_end=end_byte,
            content_length=content_length,
            mime_type=mime_type,
        )

        def file_generator():
            """
            Generator that yields file chunks with optimizations for concurrent requests.

            Features:
            - Efficient chunked reading to minimize memory usage
            - Proper error handling and logging
            - Support for large files without loading into memory
            """
            try:
                with open(path, 'rb') as f:
                    f.seek(start_byte)
                    bytes_remaining = content_length
                    bytes_sent = 0

                    while bytes_remaining > 0:
                        # Adaptive chunk sizing for better concurrent performance
                        chunk_size_actual = min(chunk_size, bytes_remaining)

                        # Read chunk
                        chunk = f.read(chunk_size_actual)

                        if not chunk:
                            # End of file reached unexpectedly
                            log_message(
                                message_type="audio_stream_unexpected_eof",
                                file_path=str(path),
                                expected_remaining=bytes_remaining,
                                total_sent=bytes_sent,
                            )
                            break

                        bytes_remaining -= len(chunk)
                        bytes_sent += len(chunk)

                        yield chunk

                    log_message(
                        message_type="audio_stream_completed",
                        file_path=str(path),
                        total_bytes_sent=bytes_sent,
                        requested_range=f"{start_byte}-{end_byte}",
                    )

            except Exception as e:
                log_message(
                    message_type="audio_stream_error",
                    file_path=str(path),
                    error=str(e),
                    error_type=type(e).__name__,
                    bytes_sent=locals().get('bytes_sent', 0),
                )
                raise

        # Set response headers with optimizations for concurrent requests
        headers = {
            'Accept-Ranges': 'bytes',
            'Content-Type': mime_type,
            'Content-Length': str(content_length),
            'Cache-Control': 'no-cache',  # Prevent caching for live streaming
            'Connection': 'keep-alive',  # Keep connection alive for concurrent requests
            'X-Content-Type-Options': 'nosniff',  # Security header
        }

        # Add Content-Range header for partial content
        if range_header:
            headers['Content-Range'] = f'bytes {start_byte}-{end_byte}/{file_size}'
            status_code = 206  # Partial Content
        else:
            status_code = 200  # OK

        return StreamingResponse(file_generator(), media_type=mime_type, headers=headers, status_code=status_code)


# Global instance
streaming_service = AudioStreamingService()
