import imghdr
from PIL import Image
import io
from typing import Tuple

def preprocess_image(image_bytes: bytes) -> bytes:
    # Validate image
    image_type = imghdr.what(None, image_bytes)
    if image_type not in ['jpeg', 'png', 'webp', 'bmp']:
        # For HEIC, we would need pillow-heif, but for now skip conversion
        if image_type == 'heic':
            raise ValueError("HEIC format not supported. Please convert to JPEG or PNG.")
        raise ValueError(f"Invalid image format: {image_type}")

    # Open image
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Failed to open image: {e}")

    # Convert to RGB (remove alpha channel)
    if image.mode in ('RGBA', 'LA', 'P'):
        image = image.convert('RGB')

    # Resize if too large
    max_size = 1600
    width, height = image.size
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * max_size / width)
        else:
            new_height = max_size
            new_width = int(width * max_size / height)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Compress to JPEG
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=85)
    output.seek(0)
    return output.getvalue()