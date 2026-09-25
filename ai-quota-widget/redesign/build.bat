@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "BUILD_MODE=%~1"
if not "%~2"=="" goto usage
if "%BUILD_MODE%"=="" goto setup
if /I "%BUILD_MODE%"=="--test-only" goto setup
if /I "%BUILD_MODE%"=="--stage-only" goto setup
:usage
echo Usage: build.bat [--test-only ^| --stage-only]
exit /b 2
:setup
set "QUOTA_CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist "%QUOTA_CSC%" set "QUOTA_CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe"
if not exist "%QUOTA_CSC%" (
    echo [ERROR] .NET Framework C# compiler not found.
    exit /b 1
)
if not exist bin mkdir bin
if /I "%BUILD_MODE%"=="--test-only" goto tests

set "QUOTA_BUILD=bin\QuotaWidget.staged-%RANDOM%-%RANDOM%.exe"
echo [BUILD] Compile staged application...
"%QUOTA_CSC%" /nologo /target:winexe /platform:anycpu /optimize+ /out:"%QUOTA_BUILD%" ^
    /r:Accessibility.dll /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Web.Extensions.dll ^
    src\*.cs
if errorlevel 1 exit /b 1

:tests
echo [TEST] Compile regression tests...
"%QUOTA_CSC%" /nologo /target:exe /main:QuotaWidget.TestMain /out:bin\QuotaTests.exe ^
    /r:Accessibility.dll /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Web.Extensions.dll ^
    src\*.cs tests\TestMain.cs tests\*Regression.cs
if errorlevel 1 exit /b 1
bin\QuotaTests.exe
if errorlevel 1 (
    echo [FAIL] Tests failed. Production executable was not replaced.
    exit /b 1
)
if /I "%BUILD_MODE%"=="--test-only" (
    echo TEST OK: production and staged executables were not changed.
    exit /b 0
)
copy /Y "%QUOTA_BUILD%" bin\QuotaWidget.next.exe >nul 2>nul
if /I "%BUILD_MODE%"=="--stage-only" (
    echo BUILD OK STAGED: %QUOTA_BUILD%
    exit /b 0
)
echo [INSTALL] Replace production executable...
copy /Y "%QUOTA_BUILD%" bin\QuotaWidget.exe >nul
if errorlevel 1 (
    echo [FAIL] Replacement failed. See the system error above; check running instances and write permissions.
    echo [INFO] Validated build is available at %QUOTA_BUILD%. No process was stopped.
    exit /b 3
)
echo BUILD OK: bin\QuotaWidget.exe
exit /b 0
