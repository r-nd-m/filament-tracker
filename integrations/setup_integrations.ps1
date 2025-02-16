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

# ✅ List available integrations (directories)
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
    $selection = Read-Host "🔢 Enter the number of the integration to set up (default: $defaultSelection)"

    if (-not $selection) { 
        $selection = $defaultSelection 
    }

    if ($selection -match "^\d+$" -and [int]$selection -ge 1 -and [int]$selection -le $integrations.Count) {
        break
    }

    Write-Host "❌ Invalid selection. Please enter a valid number (1-$($integrations.Count))."
} while ($true)

# ✅ Get selected integration name
$selectedIntegration = $integrations[[int]$selection - 1]
Write-Host "✅ Selected: $selectedIntegration"

# ✅ Determine base integration if a hidden file exists
# Default: use the selected integration as its own base.
$baseIntegrationName = $selectedIntegration
$selectedIntegrationPath = "$integrationsDir\$selectedIntegration"
$hiddenFiles = Get-ChildItem -Path $selectedIntegrationPath -Force -File | Where-Object { $_.Name -like ".*" -and $_.Name -notin ".env", ".env.example" }
if ($hiddenFiles.Count -gt 0) {
    # Assume the first hidden file indicates the base integration (strip the leading dot)
    $baseIntegrationName = $hiddenFiles[0].Name.TrimStart(".")
    Write-Host "🔍 Detected hidden file '$($hiddenFiles[0].Name)' - using '$baseIntegrationName' as the base integration."
}

# Verify that the base integration folder exists in the integrations directory
$baseIntegrationPath = "$integrationsDir\$baseIntegrationName"
if (-not (Test-Path $baseIntegrationPath)) {
    Write-Host "❌ Base integration folder '$baseIntegrationName' not found in '$integrationsDir'."
    Pause
    exit
}

# ✅ Set installation directory
$defaultInstallPath = "$env:LOCALAPPDATA\FilaTrack\$selectedIntegration"
$installPath = Read-Host "🔤 Enter installation folder (default: $defaultInstallPath)"
if (-not $installPath) { $installPath = $defaultInstallPath }

# ✅ Check if the installation folder already exists and contains configuration
$folderExists = Test-Path "$installPath"
$hasEnvFile = Test-Path "$installPath\.env"
$hasPostScript = Get-ChildItem -Path "$installPath" -Filter "*_post.py" -File -ErrorAction SilentlyContinue

if ($folderExists -and $hasEnvFile -and $hasPostScript) {
    Write-Host "⚠️  Existing installation detected at $installPath."
    $choice = Read-Host "🔁 Use existing configuration? (Y = keep existing, N = overwrite) [Default: Y]"
    if ($choice -match "^[Nn]$") {
        Write-Host "🔄 Overwriting existing installation..."
        Remove-Item -Recurse -Force "$installPath"
        New-Item -Path "$installPath" -ItemType Directory | Out-Null
        Copy-Item -Path "$baseIntegrationPath\*" -Destination "$installPath" -Recurse -Force
    } else {
        Write-Host "✅ Keeping existing installation."
    }
} else {
    Write-Host "📂 Installing integration in: $installPath"
    New-Item -Path "$installPath" -ItemType Directory | Out-Null
    Copy-Item -Path "$baseIntegrationPath\*" -Destination "$installPath" -Recurse -Force
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
if ($envFile -match 'FILAMENT_TRACKER_API_URL="?([^"\r\n]+)"?') {
    $currentApiUrl = $matches[1].Trim()
} else {
    $currentApiUrl = ""
}
$apiUrl = Read-Host "🔤 Enter Filament Tracker API URL (default: $currentApiUrl)"
if (-not $apiUrl) { $apiUrl = $currentApiUrl }

# ✅ Ask if ArcWelder is used
$useArcWelder = Read-Host "➡️  Is ArcWelder used? (Y/n) [Default: Y]"
if ($useArcWelder -match "^[Nn]$") {
    $useArcWelder = $false
} else {
    $useArcWelder = $true
}

# ✅ Read & update ARCWELDER_PATH if needed
if ($envFile -match 'ARCWELDER_PATH="?([^"\r\n]+)"?') {
    $currentArcWelderPath = $matches[1].Trim()
} else {
    $currentArcWelderPath = ""
}
if ($useArcWelder) {
    $arcWelderPath = Read-Host "🔤 Enter ArcWelder path (default: $currentArcWelderPath)"
    if (-not $arcWelderPath) { $arcWelderPath = $currentArcWelderPath }
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

# ✅ If the source integration is different from the selected integration, rename post-processing script
if ($baseIntegrationName -ne $selectedIntegration) {
    # The expected original post-processing script is named like "Prusa_post.py"
    $originalScript = Join-Path $installPath ("$baseIntegrationName" + "_post.py")
    $newScript = Join-Path $installPath ("$selectedIntegration" + "_post.py")
    if (Test-Path $originalScript) {
        Rename-Item -Path $originalScript -NewName (Split-Path $newScript -Leaf) -Force
        Write-Host "🔄 Renamed post-processing script from '$($baseIntegrationName)_post.py' to '$($selectedIntegration)_post.py'."
    }
}

# ✅ Print Slicer command if applicable
if ($selectedIntegration -eq "prusa" -or $selectedIntegration -eq "orca" -or $selectedIntegration -eq "anycubic" -or $selectedIntegration -eq "cura") {
    $scriptPath = Join-Path $installPath ("$selectedIntegration" + "_post.py")
    $cmd = "`"$pythonPath`" `"$scriptPath`""
    if ($useArcWelder) { $cmd += " -a" }
    $slicerName = ($selectedIntegration.Substring(0,1).ToUpper() + $selectedIntegration.Substring(1).ToLower())
    Write-Host "🔧 Add this command to $slicerName Slicer in Post-processing scripts:"
    Write-Host "`n$cmd;"
}

Write-Host "`n🎉 Installation complete!"
Set-Location $originalDir
Pause
