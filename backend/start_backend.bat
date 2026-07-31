@echo off
cd /d D:\Moza\backend

rem Set PYTHONPATH
SET PYTHONPATH=%cd%;%PYTHONPATH%

rem Start the backend
python -c "
import sys
import os
os.chdir('%cd%')
sys.path.insert(0, '%cd%')

try:
    from moza.main import app
    import uvicorn
    print('Starting MOZA Backend...')
    print('Server running on: http://localhost:8001')
    print('Press Ctrl+C to stop')
    uvicorn.run(app, host='0.0.0.0', port=8001, log_level='info')
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'Runtime error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

pause