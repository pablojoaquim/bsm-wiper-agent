
# BSM Wiper Agent
# ASPICE repository structure migration

$ErrorActionPreference = "Stop"

$projectRoot = "C:\jpablo\00_Projects\bsm-wiper-agent"

Set-Location $projectRoot

Write-Host "`n=== BSM Wiper Agent - ASPICE Migration ===" -ForegroundColor Cyan

# --------------------------------------------------
# Helper: move a file only when the source exists.
# --------------------------------------------------

function Move-ProjectFile {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (Test-Path -LiteralPath $Source) {

        if (Test-Path -LiteralPath $Destination) {
            throw "Destination already exists: $Destination"
        }

        $destinationDirectory = Split-Path $Destination -Parent

        New-Item -ItemType Directory -Force -Path $destinationDirectory |
            Out-Null

        Move-Item -LiteralPath $Source -Destination $Destination

        Write-Host "MOVED: $Source -> $Destination" -ForegroundColor Green
    }
}

# --------------------------------------------------
# 1. Create ASPICE process directories.
# --------------------------------------------------

$directories = @(
    "processes\SYS.2_system_requirements_analysis",
    "processes\SYS.3_system_architectural_design",
    "processes\SWE.1_software_requirements_analysis",
    "processes\SWE.2_software_architectural_design",
    "processes\SWE.3_software_detailed_design",
    "processes\SWE.4_software_unit_verification",
    "processes\SWE.5_software_integration_verification",
    "processes\SWE.6_software_qualification_test",
    "src\agents",
    "models\SWE.3",
    "generated\SWE.3\simulation_c",
    "tests\application",
    "tests\agents"
)

foreach ($directory in $directories) {
    New-Item -ItemType Directory -Force -Path $directory |
        Out-Null
}

Write-Host "`nProcess directories created." -ForegroundColor Green

# --------------------------------------------------
# 2. Move requirements artifacts.
# --------------------------------------------------

Move-ProjectFile `
    "requirements\system\bsm_system_requirements.yaml" `
    "processes\SYS.2_system_requirements_analysis\SYS.2_system_requirements.yaml"

Move-ProjectFile `
    "requirements\software\bsm_software_requirements.yaml" `
    "processes\SWE.1_software_requirements_analysis\SWE.1_software_requirements.yaml"

# --------------------------------------------------
# 3. Rename Requirements Agent.
# --------------------------------------------------

Move-ProjectFile `
    "src\agents\requirements_agent.py" `
    "src\agents\SWE1_software_requirements_agent.py"

# --------------------------------------------------
# 4. Move Modelica model.
# --------------------------------------------------

Move-ProjectFile `
    "models\BSMWiperController.mo" `
    "models\SWE.3\BSMWiperController.mo"

# Move test model if it already exists.
Move-ProjectFile `
    "models\BSMWiperTest.mo" `
    "models\SWE.3\BSMWiperTest.mo"

# --------------------------------------------------
# 5. Rename OpenModelica script.
# --------------------------------------------------

Move-ProjectFile `
    "scripts\generate_c.mos" `
    "scripts\SWE.3_generate_simulation_code.mos"

# --------------------------------------------------
# 6. Move existing generated C files.
# --------------------------------------------------

$oldGenerated = "generated\c"
$newGenerated = "generated\SWE.3\simulation_c"

if (Test-Path -LiteralPath $oldGenerated) {

    Get-ChildItem -LiteralPath $oldGenerated -Force |
        ForEach-Object {

            $destination = Join-Path $newGenerated $_.Name

            if (Test-Path -LiteralPath $destination) {
                throw "Generated file already exists: $destination"
            }

            Move-Item -LiteralPath $_.FullName -Destination $destination
        }

    # Remove old directory if empty.
    if ((Get-ChildItem -LiteralPath $oldGenerated -Force).Count -eq 0) {
        Remove-Item -LiteralPath $oldGenerated
    }

    Write-Host "Generated C files migrated." -ForegroundColor Green
}

# --------------------------------------------------
# 7. Update source-code path references.
# --------------------------------------------------

$replacements = @(
    @{
        Old = "requirements/system/bsm_system_requirements.yaml"
        New = "processes/SYS.2_system_requirements_analysis/SYS.2_system_requirements.yaml"
    },
    @{
        Old = "requirements\system\bsm_system_requirements.yaml"
        New = "processes\SYS.2_system_requirements_analysis\SYS.2_system_requirements.yaml"
    },
    @{
        Old = "requirements/software/bsm_software_requirements.yaml"
        New = "processes/SWE.1_software_requirements_analysis/SWE.1_software_requirements.yaml"
    },
    @{
        Old = "requirements\software\bsm_software_requirements.yaml"
        New = "processes\SWE.1_software_requirements_analysis\SWE.1_software_requirements.yaml"
    },
    @{
        Old = "requirements_agent"
        New = "SWE1_software_requirements_agent"
    },
    @{
        Old = "models/BSMWiperController.mo"
        New = "models/SWE.3/BSMWiperController.mo"
    },
    @{
        Old = "models\BSMWiperController.mo"
        New = "models\SWE.3\BSMWiperController.mo"
    },
    @{
        Old = "models/BSMWiperTest.mo"
        New = "models/SWE.3/BSMWiperTest.mo"
    },
    @{
        Old = "models\BSMWiperTest.mo"
        New = "models\SWE.3\BSMWiperTest.mo"
    },
    @{
        Old = "generated/c"
        New = "generated/SWE.3/simulation_c"
    },
    @{
        Old = "generated\c"
        New = "generated\SWE.3\simulation_c"
    }
)

$extensions = @(
    "*.py",
    "*.mos",
    "*.yaml",
    "*.yml",
    "*.json",
    "*.toml"
)

$files = Get-ChildItem -Path $projectRoot -Recurse -File -Include $extensions |
    Where-Object {
        $_.FullName -notmatch '[\\/]\.venv[\\/]' -and
        $_.FullName -notmatch '[\\/]\.git[\\/]'
    }

foreach ($file in $files) {

    $content = Get-Content -LiteralPath $file.FullName -Raw

    # Skip empty files.
    if ($null -eq $content) {
        continue
    }

    $originalContent = $content

    foreach ($replacement in $replacements) {
        $content = $content.Replace(
            $replacement.Old,
            $replacement.New
        )
    }

    if ($content -ne $originalContent) {

        Set-Content `
            -LiteralPath $file.FullName `
            -Value $content `
            -Encoding utf8

        Write-Host "UPDATED: $($file.FullName)" -ForegroundColor Yellow
    }
}

# --------------------------------------------------
# 8. Create placeholders for future process folders.
# --------------------------------------------------

$futureFolders = @(
    "processes\SYS.3_system_architectural_design",
    "processes\SWE.2_software_architectural_design",
    "processes\SWE.3_software_detailed_design",
    "processes\SWE.4_software_unit_verification",
    "processes\SWE.5_software_integration_verification",
    "processes\SWE.6_software_qualification_test"
)

foreach ($folder in $futureFolders) {

    $placeholder = Join-Path $folder ".gitkeep"

    if (-not (Test-Path -LiteralPath $placeholder)) {
        New-Item -ItemType File -Path $placeholder |
            Out-Null
    }
}

# --------------------------------------------------
# 9. Migration summary.
# --------------------------------------------------

Write-Host "`n=== Migration completed ===" -ForegroundColor Cyan

Write-Host "`nCurrent project directories:" -ForegroundColor Cyan

Get-ChildItem -Directory |
    Select-Object -ExpandProperty Name

Write-Host "`nCheck remaining old paths manually before running." -ForegroundColor Yellow
