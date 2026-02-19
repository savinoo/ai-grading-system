import logging
import sys
from pathlib import Path

def setup_logging(level=logging.INFO, log_file="program_flow.log"):
    """
    Configures logging to output to both console and a file.
    """
    # Create a custom logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Create formatters and handlers
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Stream Handler (Console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Suppress noisy checks
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)

    logger.info(f"Logging configured. Writing to {log_file}")
