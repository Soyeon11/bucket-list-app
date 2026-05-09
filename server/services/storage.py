"""
Supabase Storage service for activity log media files.

Handles signed upload URL generation and signed view URL generation
for the private 'logs' storage bucket.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List
from uuid import UUID

from schemas.log import SignedUploadUrl, UploadFileSpec

logger = logging.getLogger(__name__)

BUCKET = "logs"


def _sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from filename."""
    name = re.sub(r"[^\w\-.]", "_", filename)
    return name[:100]  # truncate to 100 chars


class StorageService:
    """Supabase Storage operations for the logs bucket."""

    def __init__(self, supabase_client: Any) -> None:
        self._db = supabase_client

    def create_signed_upload_urls(
        self,
        user_id: UUID,
        item_id: UUID,
        log_id: UUID,
        file_specs: List[UploadFileSpec],
    ) -> List[SignedUploadUrl]:
        """
        Generate signed PUT URLs for direct client-to-Storage upload.
        Path: {user_id}/{item_id}/{log_id}/{order}_{filename}
        """
        results: List[SignedUploadUrl] = []
        for spec in file_specs:
            safe_name = _sanitize_filename(spec.filename)
            storage_path = f"{user_id}/{item_id}/{log_id}/{spec.order}_{safe_name}"
            response = self._db.storage.from_(BUCKET).create_signed_upload_url(storage_path)
            signed_url = response.get("signedURL") or response.get("signed_url", "")
            results.append(
                SignedUploadUrl(
                    storage_path=storage_path,
                    signed_url=signed_url,
                    order=spec.order,
                    filename=spec.filename,
                )
            )
        return results

    def get_signed_view_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Generate a signed GET URL for viewing a stored file."""
        response = self._db.storage.from_(BUCKET).create_signed_url(storage_path, expires_in)
        return response.get("signedURL") or response.get("signed_url", "")

    def delete_file(self, storage_path: str) -> None:
        """Delete a file from the logs bucket."""
        try:
            self._db.storage.from_(BUCKET).remove([storage_path])
        except Exception as exc:
            logger.warning("Failed to delete storage file %s: %s", storage_path, exc)
