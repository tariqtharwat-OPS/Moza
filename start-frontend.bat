@echo off
cd /d D:\Moza\frontend
echo Starting frontend dev server on port 3000...
call npm run dev
echo Server exited with code %ERRORLEVEL%
