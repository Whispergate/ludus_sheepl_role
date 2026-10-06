# Sheepl phishing intake handler.
#
# The facilities-manager NPC "reviews" whatever document most recently landed in
# its Downloads (intake) folder. In the scenario the operator submits a contract
# document through the vendor portal and it drops here; this makes the NPC open
# it, which is the deterministic initial-access foothold. Benign on its own (it
# just opens the newest document); it only lands a beacon when the attacker's
# submitted payload is the newest file. Runs in the NPC's own interactive
# session via the Sheepl scheduled task, so it opens as that user.
$ErrorActionPreference = 'SilentlyContinue'
$dir = Join-Path $env:USERPROFILE 'Downloads'
if (-not (Test-Path -LiteralPath $dir)) { return }
$doc = Get-ChildItem -File -Path $dir |
    Where-Object { $_.Extension -in '.lnk', '.pdf', '.doc', '.docx', '.hta', '.xls', '.xlsx' } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if ($doc) { Invoke-Item -LiteralPath $doc.FullName }
