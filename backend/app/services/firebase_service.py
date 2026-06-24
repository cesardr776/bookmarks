import base64
import io
import os
import uuid
from typing import Optional

import firebase_admin
from firebase_admin import credentials, storage

_initialized = False


def _get_app() -> Optional[firebase_admin.App]:
    global _initialized
    if _initialized:
        return firebase_admin.get_app()

    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "")

    if not cred_path or not bucket_name:
        return None

    cred = credentials.Certificate(cred_path)
    app = firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})
    _initialized = True
    return app


def upload_base64_image(b64_image: str, user_id: Optional[str] = None) -> str:
    app = _get_app()
    if app is None:
        # Firebase not configured — return data URI so the app still works
        return f"data:image/jpeg;base64,{b64_image}"

    image_bytes = base64.b64decode(b64_image)
    file_id = uuid.uuid4().hex
    path = f"generated/{user_id or 'anonymous'}/{file_id}.jpg"

    bucket = storage.bucket()
    blob = bucket.blob(path)
    blob.upload_from_string(image_bytes, content_type="image/jpeg")
    blob.make_public()

    return blob.public_url
