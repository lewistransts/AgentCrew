import logging
import sys

# Create a logger
logger = logging.getLogger("AgentCrew")
logger.setLevel(logging.ERROR)  # Set default level to DEBUG

# Create a console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.ERROR)  # Set handler level

# Create a formatter and set it for the handler
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
)
ch.setFormatter(formatter)

# Add the handler to the logger
if not logger.handlers:
    logger.addHandler(ch)

# Optional: Prevent duplicate logging if this module is imported multiple times
logger.propagate = False
