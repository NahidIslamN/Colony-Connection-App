import logging

logger = logging.getLogger(__name__)


# Placeholder hook for asynchronous antivirus integration.
# This can later dispatch a Celery task without changing call sites.
def enqueue_file_scan(file_path: str, context: dict | None = None) -> None:
    logger.info("Queued file for security scan", extra={"file_path": file_path, "context": context or {}})
