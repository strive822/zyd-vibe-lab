@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem ---- 定位 .NET Framework 自带的 C# 编译器（零安装依赖） ----
set "CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist "%CSC%" set "CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe"
if not exist "%CSC%" (
    echo [ERROR] 未找到 .NET Framework 4.x 自带的 csc.exe，请确认系统为 Windows 10/11。
    exit /b 1
)

if not exist bin mkdir bin

echo [1/3] 编译 bin\QuotaWidget.exe ...
"%CSC%" /nologo /target:winexe /platform:anycpu /optimize+ /out:bin\QuotaWidget.exe ^
    /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Web.Extensions.dll ^
    src\Program.cs src\WidgetForm.cs src\Providers.cs src\Config.cs
if errorlevel 1 (
    echo [FAIL] 主程序编译失败
    exit /b 1
)

echo [2/3] 编译解析单测 bin\QuotaTests.exe ...
"%CSC%" /nologo /target:exe /out:bin\QuotaTests.exe ^
    /r:System.dll /r:System.Core.dll /r:System.Web.Extensions.dll ^
    src\Providers.cs tests\TestMain.cs
if errorlevel 1 (
    echo [FAIL] 单测编译失败
    exit /b 1
)

echo [3/3] 运行解析单测 ...
bin\QuotaTests.exe
if errorlevel 1 (
    echo [FAIL] 解析单测未通过
    exit /b 1
)

echo.
echo BUILD OK --^> bin\QuotaWidget.exe
endlocal
