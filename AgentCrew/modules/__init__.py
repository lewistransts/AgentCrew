import logging
import sys

LOG_LEVEL = logging.ERROR
# Create a logger
logger = logging.getLogger("AgentCrew")
logger.setLevel(LOG_LEVEL)  # Set default level to DEBUG

# Create a console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(LOG_LEVEL)  # Set handler level

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
