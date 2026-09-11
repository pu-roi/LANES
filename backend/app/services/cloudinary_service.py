import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from typing import Optional

from app.core.config import settings

# Initialize Cloudinary configuration
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

def upload_image(file: UploadFile) -> Optional[str]:
    """
    Uploads an image or video to Cloudinary.
    Returns the secure URL of the uploaded media.
    """
    try:
        is_video = False
        if file.content_type and file.content_type.startswith("video/"):
            is_video = True
        elif file.filename and any(file.filename.lower().endswith(ext) for ext in [".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"]):
            is_video = True

        if is_video:
            response = cloudinary.uploader.upload(
                file.file,
                folder="lanes_flood_reports",
                resource_type="video"
            )
        else:
            response = cloudinary.uploader.upload(
                file.file,
                folder="lanes_flood_reports",
                resource_type="image",
                transformation=[
                    {"width": 1200, "crop": "limit"},
                    {"fetch_format": "auto", "quality": "auto"}
                ]
            )
        return response.get("secure_url")
    except Exception as e:
        print(f"Error uploading media to Cloudinary: {e}")
        return None
