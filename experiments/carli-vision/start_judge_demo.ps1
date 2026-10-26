param(
    [string]$PythonExecutable,
    [switch]$VerifyOnly
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Find-DemoPython {
    $probe = "import sys; assert sys.implementation.name == 'cpython' and (3,12) <= sys.version_info[:2] < (3,15) and sys.maxsize > 2**32; print(sys.executable)"
    $candidates = @()
    if ($PythonExecutable) {
        $candidates += @{ Command = $PythonExecutable; Arguments = @() }
    } else {
        $candidates += @{ Command = (Join-Path $PSScriptRoot '.venv/Scripts/python.exe'); Arguments = @() }
        foreach ($version in @('3.12', '3.13', '3.14')) {
            $candidates += @{ Command = 'py'; Arguments = @("-$version") }
        }
        $candidates += @{ Command = 'python'; Arguments = @() }
        $candidates += @{ Command = 'python3'; Arguments = @() }
    }
    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Command -ErrorAction SilentlyContinue)) { continue }
        try {
            $arguments = @($candidate.Arguments) + @('-c', $probe)
            $resolved = & $candidate.Command @arguments 2>$null
            if ($LASTEXITCODE -eq 0 -and $resolved) { return ([string]($resolved | Select-Object -Last 1)).Trim() }
        } catch { continue }
    }
    throw 'No supported 64-bit CPython found (3.12, 3.13 or 3.14). Run py -0p to list installations, or pass -PythonExecutable C:\path\to\python.exe.'
}
$selectedPython = Find-DemoPython
Write-Host "Using Python: $selectedPython"
& $selectedPython --version
$demoPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if ($selectedPython -ne $demoPython) {
    if (Test-Path '.venv') {
        throw 'An existing .venv was not selected. Preserve it by renaming that folder, then rerun with -PythonExecutable. No files were deleted.'
    }
    & $selectedPython -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment setup failed.' }
}
& $demoPython -m pip install -r requirements-aws.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $demoPython -W error::ResourceWarning -m unittest discover -s . -p 'test_*.py' -v
if ($LASTEXITCODE -ne 0) { throw 'Regression failed. Demo was not started.' }
& $demoPython generate_demo_clips.py
if ($LASTEXITCODE -ne 0) { throw 'Synthetic clip generation failed.' }
if ($VerifyOnly) { Write-Host 'Verification completed; server was not started.'; exit 0 }
Write-Host 'Select a SYNTHETIC clip from demo-fixtures, or use your own consented footage.'
Write-Host 'This starts a local demo only. It does not deploy, sign in to AWS or submit to Devpost.'
& $demoPython review_demo.py
