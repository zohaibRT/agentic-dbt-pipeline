@echo off
setlocal
REM Enterprise-safe launcher: blocked until REPORT_HANDOFF_READINESS open_allowed=true
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%\..\..\..\..") do set "PROJECT_ROOT=%%~fI"
set "HANDOFF_CHECK="
if exist "%PROJECT_ROOT%\scripts\check_report_handoff_readiness.py" set "HANDOFF_CHECK=%PROJECT_ROOT%\scripts\check_report_handoff_readiness.py"
if not defined HANDOFF_CHECK if exist "%SCRIPT_DIR%\..\..\..\..\..\scripts\check_report_handoff_readiness.py" set "HANDOFF_CHECK=%SCRIPT_DIR%\..\..\..\..\..\scripts\check_report_handoff_readiness.py"

if not defined HANDOFF_CHECK (
  echo Report artifacts were generated, but the report is not ready to open.
  echo Runtime and browser verification are still pending.
  echo Missing check_report_handoff_readiness.py
  exit /b 1
)

python "%HANDOFF_CHECK%" --root "%PROJECT_ROOT%" --phase final --require-pass
if errorlevel 1 (
  echo.
  echo Report artifacts were generated, but the report is not ready to open.
  echo Runtime and browser verification are still pending.
  echo See reports\agent\10_presentation\REPORT_HANDOFF_READINESS.json
  exit /b 1
)

set "PORT=8765"
start "report-server" /B python "%SCRIPT_DIR%serve_report.py" --host 127.0.0.1 --port %PORT%
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:%PORT%/"
echo Verified report handoff: opened http://127.0.0.1:%PORT%/
exit /b 0
