@echo off
cd D:\Moza\backend
rem Set PYTHONPATH
SET PYTHONPATH=D:\Moza\backend;%PYTHONPATH%

rem Clear any existing log files
if exist server_out.log del server_out.log
if exist server_err.log del server_err.log

rem Start the backend
python moza\\main.py > server_out.log 2> server_err.log

rem Keep console open
pause
