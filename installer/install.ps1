$ErrorActionPreference = "Stop"
$Harness = Join-Path $PSScriptRoot "harness.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $Harness @args
    exit $LASTEXITCODE
}
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    & python3 $Harness @args
    exit $LASTEXITCODE
}
& python $Harness @args
exit $LASTEXITCODE
