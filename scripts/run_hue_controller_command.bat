@echo off

SET PROJECT_ROOT_DIRECTORY=%~dp0..
SET PYTHON_EXE_PATH=%PROJECT_ROOT_DIRECTORY%\.venvw\Scripts\python.exe
%PYTHON_EXE_PATH% %PROJECT_ROOT_DIRECTORY%\src\app.py %*
