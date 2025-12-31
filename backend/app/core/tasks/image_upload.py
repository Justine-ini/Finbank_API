from typing import TypedDict
import uuid
import cloudinary
import cloudinary.uploader
from backend.app.core.celery_app import celery_app
from backend.app.core.logging import get_logger
from backend.app.core.config import settings

logger = get_logger()


class UploadResponse(TypedDict):
    url: str
    image_type: str
    public_id: str
    thumbnail_url: str | None


@celery_app.task(
    name="upload_profile_image_task",
    bind=True,
    max_retries=3,
    soft_time_limit=10,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
)
def upload_profile_image_task(
    self, file_data: bytes, image_type: str, user_id: str, content_type: str
) -> UploadResponse:
    try:
        logger.info(
            f"Starting image upload for the user {user_id}, type: {image_type}")

        if content_type not in settings.ALLOWED_MIME_TYPES:
            error_msg = f"File type {content_type} is not allowed. Allowed types: {', '.join(settings.ALLOWED_MIME_TYPES)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        file_size_mb = len(file_data) / (1024 * 1024)
        max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)

        if file_size_mb > max_size_mb:
            error_msg = f"File size {file_size_mb:.2f} MB exceeds the maximum allowed size of {max_size_mb:.2f} MB"
            logger.error(error_msg)
            raise ValueError(error_msg)

        upload_options = {
            "resource_type": "image",
            "folder": f"{settings.CLOUDINARY_CLOUD_NAME}/profiles/{user_id}",
            "public_id": f"{image_type}_{str(uuid.uuid4())}",
            "overwrite": True,
            "allowed_formats": ["jpg", "jpeg", "png"],
            "eager": [
                {"width": 800, "height": 800, "crop": "limit"},
                {"width": 200, "height": 200, "crop": "fill"},
            ],
            "tags": [f"user_profile_{user_id}", image_type],
            "quality": "auto:good",
            "fetch_format": "auto",
        }
        logger.info(
            f"Uploading image to Cloudinary with options: {upload_options}")

        upload_result = cloudinary.uploader.upload(
            file_data, **upload_options,)
        logger.debug(f"Cloudinary upload result: {upload_result}")

        if not upload_result.get('secure_url'):
            raise Exception(
                "Upload successful but secure URL not received from Cloudinary.")

        response: UploadResponse = {
            "url": upload_result['secure_url'],
            "image_type": image_type,
            "public_id": upload_result['public_id'],
            "thumbnail_url": (
                upload_result.get('eager', [{}])[1].get('secure_url')
                if len(upload_result.get('eager', [])) > 1
                else None
            ),
        }
        for key in ["url", "image_type", "public_id"]:
            if not response.get(key):
                raise Exception(
                    f"Required field {key} missing in upload response")

        logger.info(
                f"Image upload successful for user {user_id}, type: {image_type}"
                f"URL: {response['url']}"
                f"Thumbnail URL: {response.get('thumbnail_url', 'No thumbnail')}"
                f"Public ID: {response['public_id']}"
            )
        return response
    except ValueError as ve:
        logger.error(f"Validation error during image upload: {str(ve)}")
        raise
    except Exception as e:
        attempt = self.request.retries + 1
        logger.error(
            f"Error uploading profile image for user {user_id}, type: {image_type}. Attempt {attempt}/{self.max_retries + 1}. Error: {str(e)}")
        if attempt <= self.max_retries:
            logger.warning(
                f"Retrying image upload for user {user_id}, type: {image_type}. "
                f"Attempt {attempt} of {self.max_retries}. Error: {str(e)}"
            )
            raise self.retry(exc=e)
        else:
            logger.error(
                f"Final upload attempt failed for user {user_id}, type: {image_type}: {str(e)}"
            )
        raise self.retry(exc=e)


