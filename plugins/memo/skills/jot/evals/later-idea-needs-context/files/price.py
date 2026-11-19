import logging

logger = logging.getLogger(__name__)


def parse_price(text: str) -> int:
    """Parse a price string like "¥1200" or "1200円" into an integer number of yen."""
    value = text.strip().lstrip("¥").rstrip("円")
    logger.info("parsed price %s", value)
    return value
