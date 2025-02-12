import os
import re
import time
import logging
import argparse
import requests
import traceback
from pathlib import Path
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler


class FileMonitorHandler(FileSystemEventHandler):
    """Handles monitoring of specific file types in a directory."""

    def __init__(self, file_extensions: list[str]) -> None:
        """Initialize the event handler with file extensions to monitor."""
        self.file_extensions = file_extensions

    def on_created(self, event: FileSystemEvent) -> None:
        """Triggered when a new file is created."""
        if not event.is_directory:
            logging.info(f"New file: {event.src_path}")
            self.process_file(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        """Triggered when a file is renamed or moved."""
        if not event.is_directory:
            logging.info(f"File renamed/moved: {event.src_path} -> {event.dest_path}")
            self.process_file(event.dest_path)

    def process_file(self, file_path: str) -> None:
        """Process file if it matches the monitored extensions."""
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in self.file_extensions:
            logging.warning(f"Detected monitored file: {file_path}")
            self.send_telegram_message(file_path)

    def send_telegram_message(self, file_path: str) -> None:
        """Send a Telegram message using the raw Telegram API via requests."""
        try:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            file_path = escape_markdown_v2(file_path)
            message = f"*⚠️ Alert\! A new monitored file was detected ⚠️*\n\n{file_path}"
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            response = requests.post(
                url, json={"chat_id": chat_id, "text": message, "parse_mode": "MarkdownV2"})

            if response.status_code == 200:
                logging.info("Telegram message sent successfully!")
            else:
                logging.error(f"Failed to send Telegram message. Response: {response.text}")

        except Exception as e:
            error_details = traceback.format_exc()
            logging.error(f"Error sending Telegram message: {repr(e)}\n{error_details}")


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram Markdown V2 formatting."""
    special_chars = r'_*[\]()~`>#+-=|{}.!'
    return re.sub(r'([{}])'.format(re.escape(special_chars)), r'\\\1', text)


def monitor_folder(folder_path: str, file_extensions: list[str]) -> None:
    """Starts monitoring the specified folder for new files matching given extensions."""

    # Create the event handler with the list of file extensions
    event_handler = FileMonitorHandler(file_extensions)

    # Initialize the watchdog observer
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=True)
    observer.start()
    logging.info("Monitoring started")

    # Send a startup message
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, json={
                  "chat_id": chat_id, "text": "*ℹ️ File monitoring script started ℹ️*", "parse_mode": "MarkdownV2"})

    try:
        # Keep the script running indefinitely
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        # Handle script termination via keyboard interrupt (Ctrl+C)
        logging.info("Monitoring stopped by user")
        requests.post(url, json={
                      "chat_id": chat_id, "text": "*🛑 File monitoring script stopped by user 🛑*", "parse_mode": "MarkdownV2"})

    except Exception as e:
        # Handle unexpected errors
        error_details = traceback.format_exc()
        logging.error(f"Unexpected error: {repr(e)}\n{error_details}")
        error_message = escape_markdown_v2(str(e))
        requests.post(url, json={
                      "chat_id": chat_id, "text": f"*⚠️ File monitoring script crashed ⚠️*\n\n{error_message}", "parse_mode": "MarkdownV2"})

    finally:
        # Ensure the observer stops gracefully
        observer.stop()
        observer.join()
        logging.info("Observer stopped")


def validate_env_vars() -> None:
    """Ensures required environment variables are set before execution."""
    required_vars = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "FOLDER_MONITOR_LIVE",
                     "FOLDER_MONITOR_DEV", "FILE_EXTENSIONS", "LOG_TYPE", "LOG_FOLDER"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)


if __name__ == "__main__":

    # Parse CLI arguments
    parser = argparse.ArgumentParser(
        description='Intrusive file monitor script')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable console logging')
    parser.add_argument('-e', '--env', help='Environment value: live / dev')
    args = parser.parse_args()

    # Load environment variables
    if args.env not in ["live", "dev"]:
        parser.error(
            "Environment value --env/-e required.\nPossible values: live / dev")

    # Load .env file
    path = Path(
        "/root/scripts/file-monitor-script/dot-env") if args.env == "live" else Path("dot-env")
    load_dotenv(dotenv_path=path)

    # Validate environment variables
    validate_env_vars()

    # Set logging format and config
    log_level = os.getenv('LOG_TYPE', 'INFO').upper()
    fmt = "%(asctime)s:%(levelname)s:%(name)s - %(message)s"
    if log_level == "DEBUG":
        logging.getLogger("httpx").setLevel(logging.INFO)
        fmt += " - {%(pathname)s:%(module)s:%(funcName)s:%(lineno)d}"

    # Set name and create the log file and folder if not exist
    log_folder = os.getenv("LOG_FOLDER", "log")
    log_file = f"{log_folder}/file-monitor-{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    Path(log_folder).mkdir(parents=True, exist_ok=True)
    Path(log_file).touch(exist_ok=True)

    # Setup the logging config
    logging.basicConfig(
        filename=log_file,
        level=getattr(logging, log_level, logging.INFO),
        format=fmt,
        datefmt='%d-%m-%Y %H:%M:%S'
    )

    # Enable console logging if verbose flag is set
    if args.verbose:
        console = logging.StreamHandler()
        console.setLevel(getattr(logging, log_level, logging.INFO))
        console.setFormatter(logging.Formatter(
            '%(levelname)s:%(name)s:%(asctime)s - %(message)s'))
        logging.getLogger("").addHandler(console)

    # Process file extensions from environment variables
    file_extensions = [ext.strip().lower() for ext in os.getenv(
        "FILE_EXTENSIONS", "").split(",") if ext.strip()]

    # Determine which folder to monitor
    folder_monitor = os.getenv(
        "FOLDER_MONITOR_LIVE") if args.env == "live" else os.getenv("FOLDER_MONITOR_DEV")

    # Start monitoring if folder exists
    if not os.path.exists(folder_monitor):
        logging.error(f"Folder does not exist: {folder_monitor}")
    else:
        logging.info(f"Monitoring folder: {folder_monitor}")
        monitor_folder(folder_monitor, file_extensions)
