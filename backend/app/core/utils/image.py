from PIL import Image, UnidentifiedImageError
import io
from typing import Tuple
from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger()

Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS


def validate_image(file_data: bytes) -> Tuple[bool, str]:
    """
    Validates an uploaded image using raw bytes.

    This function ensures:
    - The file is not empty
    - The file size is within allowed limits
    - The file is a real image (not a renamed file)
    - The image format is supported
    - The image dimensions are within limits
    - The image is fully readable (not truncated or corrupted)

    Returns:
        (bool, str): Validation result and message
    """
    try:

        # Check if file is empty
        if not file_data or len(file_data) == 0:
            return (False, "Image file is empty or corrupted.")

        # Check if file size exceeds the maximum allowed size
        file_size_mb = len(file_data) / (1024 * 1024)
        max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)

        if file_size_mb > max_size_mb:
            return (False, f"File size {file_size_mb:.2f} MB exceeds the maximum allowed size of {max_size_mb:.2f} MB")

        image_stream = io.BytesIO(file_data)

        # Open and verify the image
        try:
            with Image.open(image_stream) as img:
                img.verify()
        except Exception as verify_error:
            return (False, f"Image file is corrupted or unreadable: {str(verify_error)}")

         # Reopen the image for further processing (verify() closes the file)
        image_stream.seek(0)  # Reset stream position to the beginning
        with Image.open(image_stream) as img:
            # Check if image format is supported
            if img.format is None or img.format.lower() not in settings.ALLOWED_IMAGE_FORMATS:
                return (False, f"Unsupported image format: {img.format}. Allowed formats are JPEG, JPG, PNG.")

        # Check if image dimensions exceed the maximum allowed dimension
            width, height = img.size
            if width > settings.MAX_DIMENSION or height > settings.MAX_DIMENSION:
                return (False, f"Image dimensions {width}x{height} exceed the maximum allowed dimension of {settings.MAX_DIMENSION}px")
            # load the image to ensure its fully readable
            try:
                img.load()
            except Exception as load_error:
                return (False, f"Image file is corrupted or unreadable: {str(load_error)}")

        return (True, "Image is valid")

    except UnidentifiedImageError:
        return (False, "File is not a valid image.")
    except Exception as e:
        logger.error(f"Error validating image: {str(e)}")
        return (False, f"Invalid image file: {str(e)}")
