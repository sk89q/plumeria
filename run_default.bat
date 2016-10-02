@echo off
if not exist config.ini (
	copy config.ini.example config.ini
)
.venv\Scripts\python plumeria-bot.py
echo 
echo Plumeria has quit!
echo If this is your first time running the bot, be sure to edit the newly created config.ini and re-run the bot. On the second run, after you've enabled plugins, then additional configuration settings will appear.
echo