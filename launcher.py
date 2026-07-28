import subprocess
import webbrowser
import time
import os
import signal

try:
    subprocess.run("Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force", shell=True)
except:
    pass

backend_cmd = 'powershell -NoExit -Command "cd D:\\Moza\\backend; python -m moza.main"'
subprocess.Popen(backend_cmd, shell=True)

time.sleep(3)

frontend_cmd = 'powershell -NoExit -Command "cd D:\\Moza\\frontend; npm run dev"'
subprocess.Popen(frontend_cmd, shell=True)

time.sleep(5)

chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'
webbrowser.get(chrome_path).open('http://localhost:3000')

print("MOZA launched successfully!")
print("Backend: http://localhost:8000")
print("Frontend: http://localhost:3000")
