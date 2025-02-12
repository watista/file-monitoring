[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white)

# Intrusive file monitor script
This projects monitors a given folder for specific file types. When such a file type is found, a message is send to a Telegram chat.


## Getting started
### Environment variables and tokens
Copy the `dot-env.template` to the root folder with the name `dot-env` and fill in the variables
```
TELEGRAM_BOT_TOKEN: The token of your Telegram Bot
TELEGRAM_CHAT_ID: User or group telegram ID
FOLDER_MONITOR_LIVE: Path to monitor live
FOLDER_MONITOR_DEV: Path to monitor dev
FILE_EXTENSIONS: List with file types to monitor, seperated with ','
LOG_TYPE: Log severity (Options are: ERROR, WARNING, INFO, DEBUG)
LOG_FOLDER: Folder for the logs to write to
```

## Setup the environment
Create the python environment and install required packages
```
cd ~./file-monitoring/
python3.9 -m venv env
source env/bin/activate
pip install -r requirements.txt
deactivate
```

## Create systemd service
Create `/etc/systemd/system/plex-download-bot.service` from `~/plex-download-bot/file-monitoring.service`

Enable and start the service
```
sudo systemctl daemon-reload
sudo systemctl enable file-monitoring.service
sudo systemctl start file-monitoring.service
```

## Usage
```
# Run the script
~./file-monitoring/env/bin/python3 ~./file-monitoring/main.py
# or
source ~./file-monitoring/env/bin/activate
python3 ~./file-monitoring/main.py

# Arguments
./main.py -h              # Show help
./main.py -v              # Show console output
./main.py --verbose       # Show console output
./main.py -e dev/live     # Set env to dev or live
./main.py --env dev/live  # Set env to dev or live

```
