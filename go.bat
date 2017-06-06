@echo ------------------------------------------------------------ > SAM.log
@date /t >> SAM.log
@echo %TIME% >> SAM.log
@echo.>> SAM.log

::@c:
::@cd \SAM

@SET PYTHONPATH=.\modules

@SET SERVER_HOST=0.0.0.0
@SET SERVER_PORT=3389
@start /wait kill.bat
::@start /wait download.bat
 
@c:\Python27\python.exe apps\server.py %*

::@exit