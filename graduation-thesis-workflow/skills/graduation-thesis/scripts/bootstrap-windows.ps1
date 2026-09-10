#requires -Version 5.1
<#! Run by the assistant, not by a novice. No global PATH edits; no admin requested. !#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ToolsDir,
    [ValidateSet('core','documents')][string]$Profile = 'core',
    [string]$PythonExe,
    [switch]$Plan,
    [switch]$NoDownload,
    [switch]$IgnoreSystemPython
)
$ErrorActionPreference = 'Stop'
$pythonVersion = '3.13.15'
$toolsRoot = [System.IO.Path]::GetFullPath($ToolsDir)
if ($toolsRoot -match '["\r\n]') { throw 'ToolsDir contains unsupported characters.' }
$installDir = Join-Path $toolsRoot ('python-' + $pythonVersion)
$environmentDir = Join-Path $toolsRoot 'venv'
$environmentPython = Join-Path $environmentDir 'Scripts\python.exe'
$arch = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
$suffix = switch ($arch) { 'AMD64' { '-amd64' }; 'ARM64' { '-arm64' }; 'x86' { '' }; default { throw "Unsupported Windows architecture: $arch" } }
$installerUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion$suffix.exe"
$packages = @('python-docx','reportlab','pymupdf','python-pptx','openpyxl','matplotlib')

function Test-Python([string]$candidate, [switch]$NeedVenv) {
    if (-not $candidate -or -not (Test-Path -LiteralPath $candidate -PathType Leaf)) { return $false }
    # Avoid the Windows Store alias, which can launch UI instead of Python.
    if ($candidate -match '\\Microsoft\\WindowsApps\\') { return $false }
    $probe = 'import sys,json,ssl; assert sys.version_info >= (3,10); print(314159)'
    if ($NeedVenv) { $probe = 'import venv,ensurepip; ' + $probe }
    try {
        $reply = & $candidate -I -c $probe 2>$null
        return ($LASTEXITCODE -eq 0 -and ($reply -contains '314159'))
    } catch { return $false }
}

$selected = $null
if ($PythonExe) {
    if (-not (Test-Python $PythonExe -NeedVenv)) { throw 'Explicit PythonExe is unusable; no fallback installation was attempted.' }
    $selected = [System.IO.Path]::GetFullPath($PythonExe)
} else {
    $candidates = @($environmentPython, (Join-Path $installDir 'python.exe'))
    foreach ($name in $(if ($IgnoreSystemPython) { @() } else { @('python.exe','python3.exe') })) {
        $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue
        if ($command) { $candidates += $command.Source }
    }
    foreach ($candidate in $candidates) {
        if (Test-Python $candidate -NeedVenv) { $selected = $candidate; break }
    }
}

if ($Plan) {
    [ordered]@{ mode='plan'; tools_dir=$toolsRoot; existing_python=$selected; download_required=($null -eq $selected); installer_url=$installerUrl; profile=$Profile; packages=$(if ($Profile -eq 'documents') {$packages} else {@()}) } | ConvertTo-Json -Depth 4
    exit 0
}
if (-not $selected -and $NoDownload) { throw 'No compatible Python; downloads disabled. No setup was performed.' }
New-Item -ItemType Directory -Path $toolsRoot -Force | Out-Null
$receipt = [ordered]@{ status='setting_up'; tools_dir=$toolsRoot; profile=$Profile; python=$null; installed_packages=@(); document_rendering_verified=$false; installer=$null }
$receiptPath = Join-Path $toolsRoot 'runtime.json'
try {
    if (-not $selected) {
        if (Test-Path -LiteralPath $installDir) { throw 'Incomplete runtime directory exists. Inspect it; do not overwrite or delete automatically.' }
        $installer = Join-Path $toolsRoot "python-$pythonVersion$suffix.exe"
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $downloaded = $false
        for ($attempt = 1; $attempt -le 2; $attempt++) {
            try {
                Invoke-WebRequest -Uri $installerUrl -OutFile $installer -UseBasicParsing -TimeoutSec 60
                $downloaded = $true
                break
            } catch { if ($attempt -eq 2) { throw } }
        }
        if (-not $downloaded) { throw 'Python download failed.' }
        $signature = Get-AuthenticodeSignature -LiteralPath $installer
        if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
            throw 'Installer signature/publisher verification failed; installer was NOT executed.'
        }
        $receipt.installer = @{ url=$installerUrl; sha256=(Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash; publisher=$signature.SignerCertificate.Subject }
        $arguments = @('/quiet', 'InstallAllUsers=0', ('TargetDir="' + $installDir + '"'), 'PrependPath=0', 'AppendPath=0', 'Include_launcher=0', 'InstallLauncherAllUsers=0', 'Shortcuts=0', 'AssociateFiles=0', 'Include_test=0', 'Include_doc=0', 'Include_tcltk=0', 'Include_pip=1')
        $process = Start-Process -FilePath $installer -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
        if ($process.ExitCode -ne 0) { throw "Python installer exit code $($process.ExitCode); inspect before continuing." }
        $selected = Join-Path $installDir 'python.exe'
        if (-not (Test-Python $selected -NeedVenv)) { throw 'Installed Python failed its probe.' }
    }
    if (-not (Test-Python $environmentPython)) {
        if (Test-Path -LiteralPath $environmentDir) { throw 'Incomplete venv exists. Inspect it; do not overwrite automatically.' }
        & $selected -I -m venv $environmentDir
        if ($LASTEXITCODE -ne 0) { throw 'Could not create isolated Python environment.' }
    }
    if (-not (Test-Python $environmentPython)) { throw 'Isolated Python failed its probe.' }
    if ($Profile -eq 'documents') {
        $imports = 'import docx,reportlab,pymupdf,pptx,openpyxl,matplotlib'
        $probePath = Join-Path $toolsRoot 'probe-documents.py'
        'import importlib.util,sys; sys.exit(0 if all(importlib.util.find_spec(m) for m in ["docx","reportlab","pymupdf","pptx","openpyxl","matplotlib"]) else 1)' | Set-Content -LiteralPath $probePath -Encoding UTF8
        & $environmentPython -I $probePath
        if ($LASTEXITCODE -ne 0) {
            if ($NoDownload) { throw 'Document packages are absent; downloads disabled.' }
            & $environmentPython -I -m pip --isolated install --disable-pip-version-check --index-url https://pypi.org/simple --only-binary=:all: --retries 1 --timeout 30 @packages
            if ($LASTEXITCODE -ne 0) { throw 'Document package installation failed; no success claimed.' }
        }
        & $environmentPython -I -c $imports
        if ($LASTEXITCODE -ne 0) { throw 'Document package import check failed.' }
        $receipt.installed_packages = @(& $environmentPython -I -m pip --isolated freeze)
        if ($LASTEXITCODE -ne 0) { throw 'Could not record installed package versions.' }
    }
    $receipt.python = $environmentPython
    $receipt.status = 'ready'
    $receipt.checked_at = (Get-Date).ToUniversalTime().ToString('o')
    $receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
    $receipt | ConvertTo-Json -Depth 5
} catch {
    $receipt.status = 'failed'
    $receipt.error = $_.Exception.Message
    $receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
    throw
}
