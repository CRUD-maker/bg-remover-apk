@echo off
title Background Remover
echo Starting with Portable Python 3.10...
python_bin\python.exe main.py
if %ERRORLEVEL% NEQ 0 pause
