import io

from PIL import Image


def _detect_image_type(image_bytes: bytes) -> str:
    """Return a normalized image type for common receipt formats."""
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if image_bytes.startswith(b"RIFF") and len(image_bytes) >= 12 and image_bytes[8:12] == b"WEBP":
        return "webp"
    if image_bytes.startswith(b"BM"):
        return "bmp"
    if len(image_bytes) >= 16 and image_bytes[4:8] == b"ftyp":
        brand = image_bytes[8:16].lower()
        if brand.startswith((b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"mif1")):
            return "heic"
    return "unknown"


def preprocess_image(image_bytes: bytes) -> bytes:
    """Validate and normalize uploaded receipt images for downstream processing."""
    image_type = _detect_image_type(image_bytes)
    if image_type not in {"jpeg", "png", "webp", "bmp"}:
        if image_type == "heic":
            raise ValueError("HEIC format not supported. Please convert to JPEG or PNG.")
        raise ValueError(f"Invalid image format: {image_type}")

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except Exception as exc:
        raise ValueError(f"Failed to open image: {exc}") from exc

    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGB")

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

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=85)
    output.seek(0)
    return output.getvalue()