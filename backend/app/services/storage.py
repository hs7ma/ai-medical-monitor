import io
import os
import logging
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)

LOCAL_STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")


class StorageService:
    def __init__(self):
        self._client: Optional[Minio] = None
        self._use_local = False
        self._local_dir = os.path.abspath(LOCAL_STORAGE_DIR)
        os.makedirs(self._local_dir, exist_ok=True)

    def _get_client(self) -> Optional[Minio]:
        if self._use_local:
            return None
        if self._client is None:
            try:
                self._client = Minio(
                    settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE,
                )
            except Exception as e:
                logger.warning("MinIO init failed, using local storage: %s", e)
                self._use_local = True
                return None
        return self._client

    def _check_minio(self) -> bool:
        if self._use_local:
            return False
        client = self._get_client()
        if client is None:
            return False
        try:
            client.bucket_exists(settings.MINIO_BUCKET)
            return True
        except Exception:
            logger.warning("MinIO not reachable, falling back to local storage")
            self._use_local = True
            return False

    def _local_path(self, storage_key: str) -> str:
        return os.path.join(self._local_dir, storage_key.replace("/", os.sep))

    def ensure_bucket(self) -> None:
        if not self._check_minio():
            os.makedirs(self._local_dir, exist_ok=True)
            return
        client = self._get_client()
        try:
            if not client.bucket_exists(settings.MINIO_BUCKET):
                client.make_bucket(settings.MINIO_BUCKET)
                logger.info("Created MinIO bucket: %s", settings.MINIO_BUCKET)
        except S3Error as e:
            logger.error("MinIO bucket error: %s", e)
            self._use_local = True

    def upload_file(self, storage_key: str, data: bytes, mime_type: str) -> bool:
        if not self._check_minio():
            try:
                path = self._local_path(storage_key)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    f.write(data)
                return True
            except Exception as e:
                logger.error("Local upload error: %s", e)
                return False
        client = self._get_client()
        try:
            client.put_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=storage_key,
                data=io.BytesIO(data),
                length=len(data),
                content_type=mime_type,
            )
            return True
        except S3Error as e:
            logger.error("Upload error: %s", e)
            return False

    def download_file(self, storage_key: str) -> Optional[bytes]:
        if not self._check_minio():
            try:
                path = self._local_path(storage_key)
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        return f.read()
                return None
            except Exception as e:
                logger.error("Local download error: %s", e)
                return None
        client = self._get_client()
        try:
            response = client.get_object(settings.MINIO_BUCKET, storage_key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error("Download error: %s", e)
            return None

    def delete_file(self, storage_key: str) -> bool:
        if not self._check_minio():
            try:
                path = self._local_path(storage_key)
                if os.path.exists(path):
                    os.remove(path)
                return True
            except Exception as e:
                logger.error("Local delete error: %s", e)
                return False
        client = self._get_client()
        try:
            client.remove_object(settings.MINIO_BUCKET, storage_key)
            return True
        except S3Error as e:
            logger.error("Delete error: %s", e)
            return False


storage_service = StorageService()
