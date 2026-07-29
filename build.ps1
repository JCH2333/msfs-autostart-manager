$ErrorActionPreference = "Stop"

pyinstaller --noconfirm --clean --onefile --windowed `
  --name "MSFS-Autostart-Manager" `
  --version-file "version_info.txt" `
  "main.py"

Write-Host "Build complete: dist\MSFS-Autostart-Manager.exe"
