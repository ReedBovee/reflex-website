@echo off
REM Builds dist\MediaBuddy.exe on any Windows PC that has Python 3.10+ installed.
cd /d "%~dp0"
python -m pip install --upgrade pyinstaller || goto :fail
python -m PyInstaller --noconfirm --onefile --windowed --name MediaBuddy MediaBuddy.py || goto :fail
echo.
echo Done. Your program is in: %~dp0dist\MediaBuddy.exe
pause
exit /b 0
:fail
echo Build failed. See the messages above.
pause
exit /b 1
