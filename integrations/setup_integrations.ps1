# Stop on errors
$ErrorActionPreference = "Stop"

# Save original location
$originalDir = Get-Location

Clear-Host

# ✅ Check if Python is installed
$pythonPath = & python -c "import sys; print(sys.executable)" 2>$null
if (-not $pythonPath) {
    Write-Host "❌ Python is not installed or not in PATH. Please install Python and try again."
    Pause
    exit
}

Write-Host "✅ Python found at: $pythonPath"

# ✅ Set integrations directory
$integrationsDir = "$PSScriptRoot"

# ✅ List available integrations
$integrations = @(Get-ChildItem -Directory -Path $integrationsDir | Select-Object -ExpandProperty Name)
if (-not $integrations) {
    Write-Host "❌ No integrations found!"
    Pause
    exit
}

Write-Host "➡️  Available integrations:"
$index = 1
$integrations | ForEach-Object { Write-Host "`t$index. $_"; $index++ }

# ✅ Ask user to select an integration
$defaultSelection = 1
do {
    # ✅ Ask for user selection with default option
    $selection = Read-Host "🔢 Enter the number of the integration to set up (default: $defaultSelection)"

    # ✅ Use default if input is empty
    if (-not $selection) { 
        $selection = $defaultSelection 
    }

    # ✅ Validate selection
    if ($selection -match "^\d+$" -and [int]$selection -ge 1 -and [int]$selection -le $integrations.Count) {
        break
    }

    Write-Host "❌ Invalid selection. Please enter a valid number (1-$($integrations.Count))."

} while ($true)  # Keep asking until valid input

# ✅ Get selected integration name
$selectedIntegration = $integrations[[int]$selection - 1]
Write-Host "✅ Selected: $selectedIntegration"

# ✅ Set installation directory
$defaultInstallPath = "$env:LOCALAPPDATA\FilaTrack\$selectedIntegration"
$installPath = Read-Host "🔤 Enter installation folder (default: $defaultInstallPath)"
if (-not $installPath) { $installPath = $defaultInstallPath }

# ✅ Check if the installation folder already exists and contains configuration
$folderExists = Test-Path "$installPath"
$hasEnvFile = Test-Path "$installPath\.env"
$hasProstScript = Test-Path "$installPath\*.py"

if ($folderExists -and $hasEnvFile -and $hasProstScript) {
    Write-Host "⚠️  Existing installation detected at $installPath."
    $choice = Read-Host "🔁 Use existing configuration? (Y = keep existing, N = overwrite) [Default: Y]"
    if ($choice -match "^[Nn]$") {
        Write-Host "🔄 Overwriting existing installation..."
        Remove-Item -Recurse -Force "$installPath"
        New-Item -Path "$installPath" -ItemType Directory | Out-Null
        Copy-Item -Path "$integrationsDir\$selectedIntegration\*" -Destination "$installPath" -Recurse -Force
    } else {
        Write-Host "✅ Keeping existing installation."
    }
} else {
    # ✅ Install fresh if folder doesn't exist
    Write-Host "📂 Installing integration in: $installPath"
    New-Item -Path "$installPath" -ItemType Directory | Out-Null
    Copy-Item -Path "$integrationsDir\$selectedIntegration\*" -Destination "$installPath" -Recurse -Force
}

# ✅ Move to installation directory
Set-Location $installPath

# ✅ Rename .env.example to .env only if we're not keeping an existing installation
if ((-not $hasEnvFile) -or (Test-Path ".env.example")) {
    Rename-Item -Path ".env.example" -NewName ".env" -Force
} elseif ($hasEnvFile) {
    Write-Host "✅ Using existing .env file."
}

# ✅ Read & update FILAMENT_TRACKER_API_URL
$envFile = Get-Content ".env" -Raw
$apiUrl = if ($envFile -match 'FILAMENT_TRACKER_API_URL="?([^"\r\n]+)"?') { $matches[1].Trim() } else { "" }
$apiUrl = Read-Host "🔤 Enter Filament Tracker API URL (default: $apiUrl)"
if (-not $apiUrl) { $apiUrl = $matches[1] }

# ✅ Ask if ArcWelder is used
$useArcWelder = Read-Host "➡️  Is ArcWelder used? (Y/n) [Default: Y]"
if ($useArcWelder -match "^[Nn]$") {
    $useArcWelder = $false
} else {
    $useArcWelder = $true
}

# ✅ Read & update ARCWELDER_PATH if needed
$arcWelderPath = if ($envFile -match 'ARCWELDER_PATH="?([^"\r\n]+)"?') { $matches[1].Trim() } else { "" }
if ($useArcWelder) {
    $arcWelderPath = Read-Host "🔤 Enter ArcWelder path (default: $arcWelderPath)"
    if (-not $arcWelderPath) { $arcWelderPath = $matches[1] }
}

# ✅ Update .env file safely
$envFile = $envFile -replace "FILAMENT_TRACKER_API_URL=.*", "FILAMENT_TRACKER_API_URL=`"$apiUrl`""
if ($useArcWelder) {
    $envFile = $envFile -replace "ARCWELDER_PATH=.*", "ARCWELDER_PATH=`"$arcWelderPath`""
} else {
    $envFile = $envFile -replace "ARCWELDER_PATH=.*", ""
}
$envFile | Set-Content ".env" -Encoding UTF8
Write-Host "✅ .env updated successfully."

# ✅ Read package names from requirements.txt
$requirementsFile = "$installPath\requirements.txt"
if (Test-Path $requirementsFile) {
    $requiredPackages = Get-Content $requirementsFile | Where-Object { $_ -match "\S" }  # Remove empty lines
} else {
    Write-Host "⚠️  Warning: requirements.txt not found! Skipping package installation."
    $requiredPackages = @()
}

# ✅ Install Python packages globally if missing
$missingPackages = $requiredPackages | Where-Object { -not (& pip show $_ 2>$null | Select-String "Version") }

if ($missingPackages) {
    Write-Host "⚠️  Installing missing Python packages globally: $($missingPackages -join ', ')"
    & pip install $missingPackages
} else {
    Write-Host "✅ All required Python packages are installed."
}

# ✅ Print Slicer command if applicable
if ($selectedIntegration -eq "prusa" -or $selectedIntegration -eq "orca") {
    $scriptPath = "$installPath\${selectedIntegration}_post.py"
    $cmd = "`"$pythonPath`" `"$scriptPath`""
    if ($useArcWelder) { $cmd += " -a" }
    $slicerName = ($selectedIntegration.Substring(0,1).ToUpper() + $selectedIntegration.Substring(1).ToLower())
    Write-Host "🔧 Add this command to $slicerName Slicer in Post-processing scripts:"
    Write-Host "`n$cmd;"
}

Write-Host "`n🎉 Installation complete!"
Set-Location $originalDir
Pause
