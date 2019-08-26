@echo off
@RD /S /Q "build/html"

CALL C:\Users\Christophe\Anaconda3\Library\bin\conda.bat activate base

CALL make html
pause