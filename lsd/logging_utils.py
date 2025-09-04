import logging
import os
from typing import Optional


def setup_logging(log_file: Optional[str] = None) -> None:
    """
    Configure application logging with fixed levels:
    - Console (stdout/stderr): INFO
    - File (if provided): DEBUG

    No user configurability (ignores env and arguments beyond file path).
    Idempotent: does not duplicate handlers; if handlers exist, updates levels.
    """
    root_logger = logging.getLogger()
    # Allow all messages; handlers will filter by their own levels
    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not root_logger.handlers:
        # Console handler at INFO
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        root_logger.addHandler(ch)

        # Optional file handler at DEBUG
        if log_file:
            try:
                parent = os.path.dirname(log_file)
                if parent and not os.path.exists(parent):
                    os.makedirs(parent, exist_ok=True)
            except Exception:
                pass
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            root_logger.addHandler(fh)
    else:
        # Update existing handlers' levels to match policy
        for h in root_logger.handlers:
            if isinstance(h, logging.FileHandler):
                h.setLevel(logging.DEBUG)
                h.setFormatter(formatter)
            else:
                h.setLevel(logging.INFO)
                h.setFormatter(formatter)
