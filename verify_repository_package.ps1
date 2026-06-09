param(
    [switch]$RunInference,
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$windowsZipName = "AutoMulti-windows-x64-20260609_revision_submission.zip"
$windowsZip = Join-Path $root ("packages\" + $windowsZipName)
$expectedWindowsSha256 = "39F2895668DE5767C6958BB6FB7DAEE54EB6390047544EC3995AE3582B0E44DA"

function Assert-File {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Missing required file: $Path"
    }
}

function Assert-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "Missing required directory: $Path"
    }
}

Assert-File $windowsZip
Assert-File (Join-Path $root "packages\AutoMulti-windows-x64-20260609_revision_submission.sha256.txt")
Assert-File (Join-Path $root "packages\AutoMulti-windows-x64-20260609_revision_submission.README.txt")
Assert-File (Join-Path $root "LICENSE_AUTOMULTI_EULA.txt")
Assert-File (Join-Path $root "THIRD_PARTY_NOTICES.md")
Assert-File (Join-Path $root "QT_LGPL_RELINKING.md")

$windowsZipInfo = Get-Item -LiteralPath $windowsZip
if ($windowsZipInfo.Length -lt 100MB) {
    throw "Windows package is unexpectedly small. Git LFS may not have downloaded the real file: $windowsZip"
}

$actualWindowsSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $windowsZip).Hash.ToUpperInvariant()
if ($actualWindowsSha256 -ne $expectedWindowsSha256) {
    throw "Windows package SHA256 mismatch. Expected $expectedWindowsSha256, got $actualWindowsSha256"
}

Write-Host "OK Windows package SHA256: $actualWindowsSha256"
Write-Host "OK proprietary EULA, third-party notice, and relinking documents are present."

$mlRoot = Join-Path $root "AutoMulti-ML-testing-package"
Assert-Directory $mlRoot

$requiredFiles = @(
    "README.md",
    "requirements.txt",
    "scripts\runtest_final_dataset.py",
    "dataset\test_inputs.csv",
    "dataset\test_coordinates.xyz",
    "dataset\test_coordinates.csv",
    "dataset\features\barrier_atom_features_basic.npz",
    "model\fold_0\best_model.pt",
    "model\fold_1\best_model.pt",
    "model\fold_2\best_model.pt",
    "model\fold_3\best_model.pt",
    "model\fold_4\best_model.pt"
)

foreach ($relativePath in $requiredFiles) {
    Assert-File (Join-Path $mlRoot $relativePath)
}

$modelFile = Get-Item -LiteralPath (Join-Path $mlRoot "model\fold_0\best_model.pt")
if ($modelFile.Length -lt 1MB) {
    throw "Model file is unexpectedly small. Git LFS may not have downloaded the real files: $($modelFile.FullName)"
}

Write-Host "OK ML package required files are present."

if ($RunInference) {
    Push-Location $mlRoot
    try {
        & $Python "scripts\runtest_final_dataset.py" "--mode" "ensemble" "--split" "test"
        if ($LASTEXITCODE -ne 0) {
            throw "ML inference command failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "Skipped ML inference. Re-run with -RunInference to execute the model check."
}

Write-Host "Reviewer submission repository verified."
