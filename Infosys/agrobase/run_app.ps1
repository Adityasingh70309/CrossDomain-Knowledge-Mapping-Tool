# Ensures Streamlit uses the project config and runs from this folder
$ErrorActionPreference = 'Stop'

# Resolve paths relative to this script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigPath = Join-Path $ScriptDir ".streamlit\config.toml"
$AppPath = Join-Path $ScriptDir "streamlit_app.py"

if (-not (Test-Path $ConfigPath)) {
  Write-Error "Config not found: $ConfigPath"
  exit 1
}
if (-not (Test-Path $AppPath)) {
  Write-Error "App not found: $AppPath"
  exit 1
}

$env:STREAMLIT_CONFIG = $ConfigPath
Write-Host "Using STREAMLIT_CONFIG=$ConfigPath"

# Optional: activate venv if you have one (uncomment and adjust path)
# & (Join-Path $ScriptDir "venv\Scripts\Activate.ps1")

# Run the app
streamlit run $AppPath