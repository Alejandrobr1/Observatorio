import logging
import sys

def get_logger(name):
    """
    Configures and returns a logger.
    """
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all messages

    # Avoid adding multiple handlers if the logger is already configured
    if not logger.handlers:
        # Create a console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)  # Log INFO and higher levels to console

        # Create a formatter and set it for the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(ch)

    return logger
