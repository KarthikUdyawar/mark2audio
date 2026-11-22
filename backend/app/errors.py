"""Domain error carrying a stable machine code, safe message and HTTP status."""

import errno


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def as_disk_full(err: BaseException) -> AppError | None:
    """Map an out-of-space OSError to a safe DISK_FULL error; None for anything else."""
    if isinstance(err, OSError) and err.errno == errno.ENOSPC:
        return AppError("DISK_FULL", "Not enough disk space.", 507)
    return None
