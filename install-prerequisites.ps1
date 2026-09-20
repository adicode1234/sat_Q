# Run this script yourself in PowerShell as Administrator.
# No automatic restart and no automatic Docker license acceptance.
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Open PowerShell as Administrator and run this script again. WSL enables Windows virtualization components.'
}
& wsl.exe --install --no-distribution
if ($LASTEXITCODE -ne 0) { Write-Warning 'WSL reported an error. Read the output above; complete WSL installation before container testing.' }
$cachedInstaller = Join-Path $PSScriptRoot '../../work/Docker Desktop Installer.exe'
$installer = if (Test-Path -LiteralPath $cachedInstaller) { (Resolve-Path -LiteralPath $cachedInstaller).Path } else { Join-Path $env:TEMP 'SatQuery-Docker-Desktop-Installer.exe' }
if (-not (Test-Path -LiteralPath $installer)) {
    Invoke-WebRequest 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe' -OutFile $installer
}
$signature = Get-AuthenticodeSignature -LiteralPath $installer
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Docker Inc') { throw 'Docker installer signature verification failed.' }
$install = Start-Process -FilePath $installer -ArgumentList @('install','--user','--quiet','--backend=wsl-2') -WindowStyle Hidden -PassThru -Wait
if ($install.ExitCode -ne 0) { throw "Docker installer exited with code $($install.ExitCode)." }
Write-Host 'Docker installer completed. Restart Windows if WSL requested it. Open Docker Desktop and review/accept its agreement yourself.'
Write-Host 'Once Docker is running, stop the native SatQuery server and run ./verify-docker.ps1 from the project folder.'
