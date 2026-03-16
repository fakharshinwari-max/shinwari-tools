@echo off
echo Starting Shinwari Tools...
call C:\Users\fakhar\tts_env\Scripts\activate
cd C:\Users\fakhar\Documents\ShinwariTools
start http://127.0.0.1:5003
python app.py
pause