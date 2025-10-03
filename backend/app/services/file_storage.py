"""
File storage service for temporary upload files
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime


class FileStorage:
    """Handle temporary file storage for uploads"""

    def __init__(self, base_path: str = "/tmp/uploads"):
        self.base_path = Path(base_path)

    def get_user_batch_path(self, user_id: str, batch_id: str) -> Path:
        """
        Get path for user's upload batch

        Args:
            user_id: User identifier
            batch_id: Batch identifier

        Returns:
            Path object for the batch directory
        """
        return self.base_path / str(user_id) / batch_id

    def create_batch_directory(self, user_id: str, batch_id: str) -> Path:
        """
        Create directory for upload batch

        Args:
            user_id: User identifier
            batch_id: Batch identifier

        Returns:
            Path to created directory
        """
        batch_path = self.get_user_batch_path(user_id, batch_id)
        batch_path.mkdir(parents=True, exist_ok=True)
        return batch_path

    def save_file(self, user_id: str, batch_id: str, filename: str, file_content: bytes) -> Path:
        """
        Save uploaded file to batch directory

        Args:
            user_id: User identifier
            batch_id: Batch identifier
            filename: Original filename
            file_content: File content as bytes

        Returns:
            Path to saved file
        """
        batch_path = self.create_batch_directory(user_id, batch_id)
        file_path = batch_path / filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        return file_path

    def get_file_path(self, user_id: str, batch_id: str, filename: str) -> Optional[Path]:
        """
        Get path to uploaded file

        Args:
            user_id: User identifier
            batch_id: Batch identifier
            filename: Original filename

        Returns:
            Path to file if it exists, None otherwise
        """
        file_path = self.get_user_batch_path(user_id, batch_id) / filename

        if file_path.exists():
            return file_path

        return None

    def cleanup_batch(self, user_id: str, batch_id: str) -> bool:
        """
        Remove batch directory and all files

        Args:
            user_id: User identifier
            batch_id: Batch identifier

        Returns:
            True if cleanup successful
        """
        batch_path = self.get_user_batch_path(user_id, batch_id)

        if batch_path.exists():
            shutil.rmtree(batch_path)
            return True

        return False

    def cleanup_old_files(self, days_old: int = 7) -> int:
        """
        Remove files older than specified days

        Args:
            days_old: Number of days after which to delete files

        Returns:
            Number of directories removed
        """
        if not self.base_path.exists():
            return 0

        removed_count = 0
        current_time = datetime.now().timestamp()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)

        for user_dir in self.base_path.iterdir():
            if not user_dir.is_dir():
                continue

            for batch_dir in user_dir.iterdir():
                if not batch_dir.is_dir():
                    continue

                # Check directory modification time
                if batch_dir.stat().st_mtime < cutoff_time:
                    shutil.rmtree(batch_dir)
                    removed_count += 1

            # Remove empty user directories
            if not any(user_dir.iterdir()):
                user_dir.rmdir()

        return removed_count


# Global instance
file_storage = FileStorage()
