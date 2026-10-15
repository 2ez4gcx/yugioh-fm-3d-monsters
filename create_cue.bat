@echo off
rem Create a .cue file for a single-track PS1 disc image (Mode2/2352).
rem Usage: drag and drop .bin files onto this file,
rem or double-click it to create a .cue for every .bin in the same folder.
setlocal DisableDelayedExpansion
cd /d "%~dp0"
if "%~1"=="" goto all_files
:each_file
if "%~1"=="" goto done
call :make "%~1"
shift
goto each_file
:all_files
set "found=0"
for %%F in (*.bin) do (set "found=1" & call :make "%%~fF")
if "%found%"=="0" echo No .bin file found in this folder.
goto done
:make
if /i not "%~x1"==".bin" (echo Skipped "%~nx1" - not a .bin file & goto :eof)
> "%~dpn1.cue" (
  echo FILE "%~nx1" BINARY
  echo   TRACK 01 MODE2/2352
  echo     INDEX 01 00:00:00
)
echo Created "%~n1.cue"
goto :eof
:done
echo.
pause
