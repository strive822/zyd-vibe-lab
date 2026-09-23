#requires -Version 5.1
<#! Assistant-run installer. Does not require Git or Python. !#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('codex','claude-code','workbuddy')][string]$Client,
    [string]$SkillsDir,
    [string]$SourceRoot,
    [switch]$Plan
)
$ErrorActionPreference = 'Stop'
if (-not $SourceRoot) { $SourceRoot = Split-Path $PSScriptRoot -Parent }
$bundleRoot = [IO.Path]::GetFullPath($SourceRoot)
$source = Join-Path $bundleRoot 'skills\graduation-thesis'
if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) { throw 'Skill source missing. Download the complete workflow folder first.' }
if (-not $SkillsDir) {
    $userRoot = [Environment]::GetFolderPath('UserProfile')
    $relative = switch ($Client) { 'codex' {'.agents\skills'}; 'claude-code' {'.claude\skills'}; 'workbuddy' {'.workbuddy\skills'} }
    $SkillsDir = Join-Path $userRoot $relative
    if ($Client -eq 'workbuddy' -and -not (Test-Path -LiteralPath $SkillsDir -PathType Container)) {
        throw 'WorkBuddy skill directory not confirmed. Inspect the host and pass its actual SkillsDir; do not guess.'
    }
}
$skillsRoot = [IO.Path]::GetFullPath($SkillsDir)
$destination = Join-Path $skillsRoot 'graduation-thesis'
if ($Plan) {
    @{mode='plan'; client=$Client; source=$source; destination=$destination} | ConvertTo-Json
    exit 0
}
$expected = @{}
foreach ($file in Get-ChildItem -LiteralPath $source -File -Recurse) {
    if ($file.FullName -match '[\\/]__pycache__[\\/]' -or $file.Extension -eq '.pyc') { continue }
    $relative = $file.FullName.Substring($source.Length).TrimStart([char[]]'\/')
    $bytes = [IO.File]::ReadAllBytes($file.FullName)
    if ($relative -eq 'SKILL.md' -and $Client -eq 'workbuddy') {
        $text = [Text.Encoding]::UTF8.GetString($bytes).Replace("`r`n", "`n")
        $boundary = $text.IndexOf("`n---`n", 3)
        if ($boundary -lt 0) { throw 'Invalid skill frontmatter.' }
        $extra = "`ndescription_zh: Evidence-based undergraduate thesis workflow`ndescription_en: Evidence-based undergraduate thesis workflow`nversion: 0.3.0`nauthor: Graduation Thesis Workflow contributors"
        $text = $text.Insert($boundary, $extra)
        $bytes = [Text.Encoding]::UTF8.GetBytes($text)
    }
    $expected[$relative] = $bytes
}
$license = Join-Path $bundleRoot 'LICENSE'
$expected['LICENSE'] = [IO.File]::ReadAllBytes($license)
if (Test-Path -LiteralPath $destination) {
    foreach ($name in $expected.Keys) {
        $path = Join-Path $destination $name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or [Convert]::ToBase64String([IO.File]::ReadAllBytes($path)) -ne [Convert]::ToBase64String($expected[$name])) {
            throw 'An existing different/incomplete skill was preserved. Inspect and back it up before an authorized update.'
        }
    }
    @{status='already_installed'; client=$Client; path=$destination; note='Host discovery must still be checked.'} | ConvertTo-Json
    exit 0
}
New-Item -ItemType Directory -Path $destination | Out-Null
foreach ($name in $expected.Keys) {
    $path = Join-Path $destination $name
    New-Item -ItemType Directory -Path (Split-Path $path -Parent) -Force | Out-Null
    [IO.File]::WriteAllBytes($path, $expected[$name])
}
foreach ($name in $expected.Keys) {
    if ([Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $destination $name))) -ne [Convert]::ToBase64String($expected[$name])) { throw 'Post-install file verification failed.' }
}
@{status='files_installed'; client=$Client; path=$destination; note='Read SKILL.md now; verify host discovery separately and refresh session only if needed.'} | ConvertTo-Json
