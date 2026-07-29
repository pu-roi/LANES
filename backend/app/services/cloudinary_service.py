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
    Uploads an image to Cloudinary, converts it to webp, and resizes it.
    Returns the secure URL of the uploaded image.
    """
    try:
        # Upload to Cloudinary with transformations
        response = cloudinary.uploader.upload(
            file.file,
            folder="lanes_flood_reports",
            resource_type="auto",
            transformation=[
                {"width": 1200, "crop": "limit"},
                {"fetch_format": "auto", "quality": "auto"}
            ]
        )
        # return the secure URL with f_auto and q_auto
        # Cloudinary URLs look like: https://res.cloudinary.com/demo/image/upload/v12345/folder/file.jpg
        # We can just return the secure_url which already has the uploaded format, 
        # but optimally we'd inject f_auto,q_auto if we want optimization.
        # For simplicity, just return the raw secure_url for now.
        return response.get("secure_url")
    except Exception as e:
        print(f"Error uploading image to Cloudinary: {e}")
        return None
