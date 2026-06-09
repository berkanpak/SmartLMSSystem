# Smart LMS Windows one-line installer
# Usage: irm https://raw.githubusercontent.com/berkanpak/SmartLMSSystem/main/install.ps1 | iex
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$RepoUrl = "https://github.com/berkanpak/SmartLMSSystem.git"
$ZipUrl = "https://github.com/berkanpak/SmartLMSSystem/archive/refs/heads/main.zip"
$InstallDir = if ($env:SMART_LMS_DIR) { $env:SMART_LMS_DIR } else { Join-Path $env:USERPROFILE ".smart-lms-app" }

function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-Python311 {
    $candidates = @(
        @("py", "-3.13"),
        @("py", "-3.12"),
        @("py", "-3.11"),
        @("python"),
        @("python3")
    )

    foreach ($candidate in $candidates) {
        $cmd = $candidate[0]
        $cmdArgs = @()
        if ($candidate.Count -gt 1) {
            $cmdArgs = $candidate[1..($candidate.Count - 1)]
        }
        if (-not (Test-Command $cmd)) {
            continue
        }

        try {
            $version = & $cmd @cmdArgs -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            $parts = "$version".Trim().Split(".")
            if ([int]$parts[0] -gt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 11)) {
                return @{ Command = $cmd; Args = $cmdArgs }
            }
        } catch {
            continue
        }
    }

    return $null
}

function Install-FromZip {
    $tmpRoot = Join-Path $env:TEMP ("smart-lms-" + [guid]::NewGuid().ToString("N"))
    $zipPath = Join-Path $tmpRoot "smart-lms.zip"
    $expanded = Join-Path $tmpRoot "expanded"

    New-Item -ItemType Directory -Force -Path $tmpRoot | Out-Null
    Invoke-WebRequest -UseBasicParsing -Uri $ZipUrl -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath $expanded -Force
    $source = Get-ChildItem -Path $expanded -Directory | Select-Object -First 1

    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    Get-ChildItem -LiteralPath $source.FullName -Force | Copy-Item -Destination $InstallDir -Recurse -Force
    Remove-Item -LiteralPath $tmpRoot -Recurse -Force
}

Write-Host ""
Write-Host "  Smart LMS MCP Installer" -ForegroundColor Cyan
Write-Host "  Target: $InstallDir" -ForegroundColor DarkGray
Write-Host ""

$python = Get-Python311
if (-not $python) {
    Write-Host "  ERROR: Python 3.11+ was not found. Install it from https://python.org, then rerun this command." -ForegroundColor Red
    exit 1
}

if ((Test-Path (Join-Path $InstallDir ".git")) -and (Test-Command "git")) {
    Write-Host "  Updating existing install..."
    git -C $InstallDir pull --quiet
} elseif (Test-Command "git") {
    if (Test-Path $InstallDir) {
        Write-Host "  Existing non-git install found. Refreshing files from GitHub zip..."
        Install-FromZip
    } else {
        Write-Host "  Cloning SmartLMSSystem..."
        git clone --quiet $RepoUrl $InstallDir
    }
} else {
    Write-Host "  Git not found. Downloading SmartLMSSystem zip..."
    Install-FromZip
}

$pythonArgs = @($python.Args) + @((Join-Path $InstallDir "install.py"), "--repo", $InstallDir) + $args
& $python.Command @pythonArgs
