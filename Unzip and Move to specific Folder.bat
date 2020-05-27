@echo off 

set USER_NAME=%username%
set DEST_PATH=E:\STUDY\new

cd /d C:\Users\%USER_NAME%\Downloads
for /f "delims=" %%i in ('dir DATA2020-* /b/a-d/od/t:c') do set ZIP_FILE_NAME=%%i
powershell -command "Expand-Archive -Force '%ZIP_FILE_NAME%' 'tempDATA'"
copy tempDATA\DATA2020 %DEST_PATH% /y
rmdir /S /Q "C:\Users\%USER_NAME%\Downloads\tempDATA"
for /f "delims=" %%i in ('dir DATA2020-* /b/a-d/od/t:c') do del "C:\Users\%USER_NAME%\Downloads\%%i"

set /p DUMMY=Task completed. Hit ENTER to continue...