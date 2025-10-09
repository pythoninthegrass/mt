import io
from pathlib import Path
from PIL import Image, ImageEnhance
from tkinter import PhotoImage
from typing import Optional


class IconLoader:
    """Handles loading and caching of icon images."""

    def __init__(self):
        self._cache = {}

    def load_icon(
        self,
        icon_path: str,
        size: tuple[int, int] | None = None,
        opacity: float = 1.0,
        tint_color: str | None = None,
    ) -> PhotoImage:
        """
        Load an icon from file with optional transformations.

        Args:
            icon_path: Path to the icon file
            size: Optional (width, height) tuple to resize the icon
            opacity: Opacity level (0.0 to 1.0)
            tint_color: Optional hex color to tint the icon (e.g., '#1CAAD9')

        Returns:
            PhotoImage object ready for tkinter use
        """
        # Create cache key from parameters
        cache_key = (icon_path, size, opacity, tint_color)

        # Return cached version if available
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Load and process the image
        img = Image.open(icon_path)

        # Resize if requested
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)

        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Apply opacity
        if opacity < 1.0:
            alpha = img.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
            img.putalpha(alpha)

        # Apply tint color
        if tint_color:
            img = self._tint_image(img, tint_color)

        # Convert to PhotoImage using a temp file approach (workaround for PIL/Tk compatibility)
        # Save to bytes buffer as PNG
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Load with tkinter's native PhotoImage
        photo_img = PhotoImage(data=buffer.read())

        # Cache the result
        self._cache[cache_key] = photo_img

        return photo_img

    def _tint_image(self, img: Image.Image, tint_color: str) -> Image.Image:
        """
        Apply a tint color to an image.

        Args:
            img: PIL Image in RGBA mode
            tint_color: Hex color string (e.g., '#1CAAD9')

        Returns:
            Tinted image
        """
        # Convert hex to RGB
        tint_color = tint_color.lstrip('#')
        r = int(tint_color[0:2], 16)
        g = int(tint_color[2:4], 16)
        b = int(tint_color[4:6], 16)

        # Create a colored overlay
        overlay = Image.new('RGB', img.size, (r, g, b))

        # Blend the overlay with the grayscale version of the image
        grayscale = img.convert('L').convert('RGB')
        blended = Image.blend(grayscale, overlay, alpha=0.5)

        # Preserve the original alpha channel
        blended = blended.convert('RGBA')
        blended.putalpha(img.split()[3])

        return blended

    def clear_cache(self):
        """Clear the icon cache."""
        self._cache.clear()


# Global icon loader instance
_icon_loader = IconLoader()


def load_icon(
    icon_path: str,
    size: tuple[int, int] | None = None,
    opacity: float = 1.0,
    tint_color: str | None = None,
) -> PhotoImage:
    """
    Convenience function to load an icon using the global loader.

    Args:
        icon_path: Path to the icon file
        size: Optional (width, height) tuple to resize the icon
        opacity: Opacity level (0.0 to 1.0)
        tint_color: Optional hex color to tint the icon (e.g., '#1CAAD9')

    Returns:
        PhotoImage object ready for tkinter use
    """
    return _icon_loader.load_icon(icon_path, size, opacity, tint_color)


def clear_icon_cache():
    """Clear the global icon cache."""
    _icon_loader.clear_cache()
