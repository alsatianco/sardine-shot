# Build sardine_shot.exe using PyInstaller
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Ensure PyInstaller is installed
try {
    python -m PyInstaller --version | Out-Null
} catch {
    Write-Host "PyInstaller not found. Installing..."
    pip install pyinstaller
}

# Clean previous build artifacts
Write-Host "Cleaning previous build..."
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist

# Build EXE
Write-Host "Building EXE..."
python -m PyInstaller `
    --onefile `
    --noconsole `
    --name sardine_shot `
    --hidden-import tkinter `
    --hidden-import tkinter.messagebox `
    --hidden-import tkinter.filedialog `
    sardine_shot.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Build successful! EXE is at: dist\sardine_shot.exe"
} else {
    Write-Host "Build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}
