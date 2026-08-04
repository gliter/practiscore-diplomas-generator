param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version,
    [string]$OutputRoot = "dist"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$buildRoot = Join-Path $repoRoot "build\windows"
$releaseRoot = Join-Path $buildRoot "release\practiscore-diplomas-generator-$Version-windows-x64"
$zipPath = Join-Path $repoRoot "$OutputRoot\practiscore-diplomas-generator-$Version-windows-x64.zip"

Push-Location $repoRoot
try {
    Remove-Item -LiteralPath $buildRoot -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $repoRoot $OutputRoot) -Force | Out-Null

    uv run pyinstaller --noconfirm --clean --onefile --name practiscore-diplomas --paths src scripts\entrypoint.py

    Copy-Item -LiteralPath (Join-Path $repoRoot "dist\practiscore-diplomas.exe") -Destination $releaseRoot
    Copy-Item -LiteralPath (Join-Path $repoRoot "LICENSE") -Destination $releaseRoot
    Copy-Item -LiteralPath (Join-Path $repoRoot "docs") -Destination $releaseRoot -Recurse
    Copy-Item -LiteralPath (Join-Path $repoRoot "configs") -Destination $releaseRoot -Recurse
    if (Test-Path (Join-Path $repoRoot "example-diploma-template.docx")) {
        Copy-Item -LiteralPath (Join-Path $repoRoot "example-diploma-template.docx") -Destination $releaseRoot
    }

    Remove-Item -LiteralPath $zipPath -Force -ErrorAction SilentlyContinue
    Compress-Archive -Path (Join-Path $releaseRoot "*") -DestinationPath $zipPath
    Write-Output "Created $zipPath"
}
finally {
    Pop-Location
}
