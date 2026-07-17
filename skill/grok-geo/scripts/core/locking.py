"""File-based exclusive locking."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Optional


def file_lock(path: Path, timeout: float = 30.0) -> "FileLock":
    return FileLock(path, timeout=timeout)


class FileLock:
    """Simple exclusive lock via lock file + atomic create (cross-platform)."""

    def __init__(self, path: Path, timeout: float = 30.0) -> None:
        self.lock_path = Path(str(path) + ".lock")
        self.timeout = timeout
        self._fd: Optional[int] = None

    def __enter__(self) -> "FileLock":
        start = time.time()
        while True:
            try:
                self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self._fd, str(os.getpid()).encode("ascii"))
                return self
            except FileExistsError:
                if time.time() - start > self.timeout:
                    raise TimeoutError(f"Could not acquire lock: {self.lock_path}")
                time.sleep(0.05)

    def __exit__(self, *args: Any) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
        try:
            self.lock_path.unlink(missing_ok=True)
        except TypeError:
            if self.lock_path.exists():
                self.lock_path.unlink()
        except OSError:
            pass