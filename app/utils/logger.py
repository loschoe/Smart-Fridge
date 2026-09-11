import logging
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "debug.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("smartfridge")
