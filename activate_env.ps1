
if (-not $env:CONDA_DEFAULT_ENV -or $env:CONDA_DEFAULT_ENV -ne "tkvj") {
    .\tkvj\Scripts\activate
}
Write-Host "[OK] Environment 'tkvj' activated." -ForegroundColor Green