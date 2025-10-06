import logging
import os

# Create logs directory if it doesn't exist
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Define log file path
log_file = os.path.join(log_dir, "application_classification_logs.log")

# Configure root logger to write to a file with appropriate format and level
logging.basicConfig(
    level=logging.INFO,  # capture all logs of INFO level and above
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler()  # Optional: also print logs to console
    ]
)