from __future__ import annotations

import logging
import os
from collections.abc import Iterable


class _SecretFilter(logging.Filter):
    def __init__(self, secret_values: Iterable[str]) -> None:
        super().__init__()
        self._secrets = [value for value in secret_values if value]

    def filter(self, record: logging.LogRecord) -> bool:
        if not self._secrets:
            return True

        message = record.getMessage()
        for secret in self._secrets:
            if secret in message:
                message = message.replace(secret, "***")
        record.msg = message
        record.args = ()
        return True


def setup_logging(level: str) -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger("app")

    secret_values = [
        os.getenv("BOT_TOKEN"),
        os.getenv("WEBHOOK_SECRET_TOKEN"),
    ]
    logger.addFilter(_SecretFilter(secret_values))
    return logger
