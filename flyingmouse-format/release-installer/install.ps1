# Download the unchanged official installer, verify it, then open its own wizard.
$ErrorActionPreference = 'Stop'
$installerPath = Join-Path $PSScriptRoot 'FlyingMouse-Format-Setup-0.8.3-x64.exe'
$expectedHash = '3a3825bd3eb751c451978c6248a52c17e122fdf708556fd7a4cc55739592ec2d'
if (-not (Test-Path -LiteralPath $installerPath)) {
    $partialPath = $installerPath + '.download'
    if (Test-Path -LiteralPath $partialPath) { throw 'An existing partial download was preserved; use a new folder.' }
    try {
        Invoke-WebRequest -Uri 'https://github.com/LaoFeng-mouse/flyingmouse-format/releases/download/v0.8.3/FlyingMouse-Format-Setup-0.8.3-x64.exe' -OutFile $partialPath -UseBasicParsing
        if ((Get-FileHash -LiteralPath $partialPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) { throw 'Official installer SHA-256 mismatch.' }
        Move-Item -LiteralPath $partialPath -Destination $installerPath
    } finally {
        if (Test-Path -LiteralPath $partialPath) { Remove-Item -LiteralPath $partialPath }
    }
}
if ((Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) { throw 'Existing installer SHA-256 mismatch; file left untouched.' }
Start-Process -FilePath $installerPath -Wait
