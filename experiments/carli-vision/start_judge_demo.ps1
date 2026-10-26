$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required. Virtual environment setup failed.' }
}
$demoPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
& $demoPython -m pip install -r requirements-aws.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $demoPython -W error::ResourceWarning -m unittest discover -s . -p 'test_*.py' -v
if ($LASTEXITCODE -ne 0) { throw 'Regression failed. Demo was not started.' }
& $demoPython generate_demo_clips.py
if ($LASTEXITCODE -ne 0) { throw 'Synthetic clip generation failed.' }
Write-Host 'Select a SYNTHETIC clip from demo-fixtures, or use your own consented footage.'
Write-Host 'This starts a local demo only. It does not deploy, sign in to AWS or submit to Devpost.'
& $demoPython review_demo.py
