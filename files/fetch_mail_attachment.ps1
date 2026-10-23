# Sheepl phishing-victim NPC handler.
#
# Checks a Mailpit or MailHog inbox for emails with file attachments,
# downloads the most recent one, and opens it. Simulates a user who reads
# a phishing email and clicks what they receive.
#
# Runs in the NPC's interactive session via the Sheepl scheduled task.
# Tracks processed message IDs so each attachment is opened only once
# across Sheepl loop iterations.
#
# Supported payload types (anything an attacker might attach):
#   Direct:     .lnk .hta .exe .msi .bat .cmd .vbs .js .wsf .scr .ps1 .com
#   Documents:  .doc .docx .docm .xls .xlsx .xlsm .pptm .pdf .rtf .one
#   Containers: .zip (extracted), .iso/.img (mounted) -- inner payload opened
#   Anything else is passed to Invoke-Item (Windows default handler).

param(
    [Parameter(Mandatory)]
    [string]$MailServerUrl,
    [string]$DownloadDir = (Join-Path $env:USERPROFILE 'Downloads')
)

$ErrorActionPreference = 'SilentlyContinue'

$base     = $MailServerUrl.TrimEnd('/')
$stateDir = Join-Path $env:ProgramData 'Sheepl'
$logFile  = Join-Path $stateDir 'processed_emails.txt'

if (-not (Test-Path $stateDir))    { New-Item -ItemType Directory -Path $stateDir -Force | Out-Null }
if (-not (Test-Path $DownloadDir)) { New-Item -ItemType Directory -Path $DownloadDir -Force | Out-Null }

$processed = @()
if (Test-Path $logFile) { $processed = @(Get-Content $logFile) }

$payloadExts = @(
    '.exe','.msi','.lnk','.hta','.bat','.cmd','.vbs','.js','.wsf',
    '.scr','.ps1','.com','.doc','.docx','.docm','.xls','.xlsx',
    '.xlsm','.pptm','.pdf','.rtf','.one'
)

function Open-Payload ([string]$Path) {
    if (-not (Test-Path $Path)) { return }
    $ext = [IO.Path]::GetExtension($Path).ToLower()

    if ($ext -eq '.zip') {
        $dest = Join-Path $DownloadDir ([IO.Path]::GetFileNameWithoutExtension($Path))
        try { Expand-Archive -LiteralPath $Path -DestinationPath $dest -Force } catch { return }
        $inner = Get-ChildItem -File $dest -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.Extension.ToLower() -in $payloadExts } |
            Select-Object -First 1
        if (-not $inner) {
            $inner = Get-ChildItem -File $dest -ErrorAction SilentlyContinue |
                Select-Object -First 1
        }
        if ($inner) { Invoke-Item -LiteralPath $inner.FullName }
        return
    }

    if ($ext -in '.iso', '.img') {
        try {
            $m = Mount-DiskImage -ImagePath $Path -PassThru -ErrorAction Stop
            $vol = $m | Get-Volume
            if ($vol.DriveLetter) {
                $root = "$($vol.DriveLetter):\"
                $inner = Get-ChildItem -File $root -ErrorAction SilentlyContinue |
                    Where-Object { $_.Extension.ToLower() -in $payloadExts } |
                    Select-Object -First 1
                if (-not $inner) {
                    $inner = Get-ChildItem -File $root -ErrorAction SilentlyContinue |
                        Select-Object -First 1
                }
                if ($inner) { Invoke-Item -LiteralPath $inner.FullName }
            }
        } catch {}
        return
    }

    Invoke-Item -LiteralPath $Path
}

# --- Detect API (Mailpit vs MailHog) ---

$messages = $null
$api      = $null

try {
    $r = Invoke-RestMethod -Uri "$base/api/v1/messages" -TimeoutSec 10
    if ($r.messages) { $messages = $r.messages; $api = 'mailpit' }
} catch {}

if (-not $messages) {
    try {
        $r = Invoke-RestMethod -Uri "$base/api/v2/messages" -TimeoutSec 10
        if ($r.items) { $messages = $r.items; $api = 'mailhog' }
    } catch {}
}

if (-not $messages) { return }

# --- Process the first unread email that has attachments ---

foreach ($msg in $messages) {
    $id = $msg.ID
    if ($id -in $processed) { continue }

    $downloaded = @()

    if ($api -eq 'mailpit') {
        if ([int]$msg.Attachments -lt 1) {
            Add-Content -Path $logFile -Value $id -Encoding utf8
            continue
        }
        try {
            $detail = Invoke-RestMethod -Uri "$base/api/v1/message/$id" -TimeoutSec 10
        } catch { continue }

        foreach ($att in $detail.Attachments) {
            $dest = Join-Path $DownloadDir $att.FileName
            if (Test-Path $dest) { continue }
            try {
                Invoke-WebRequest -Uri "$base/api/v1/message/$id/part/$($att.PartID)" `
                    -OutFile $dest -TimeoutSec 30 -UseBasicParsing
                $downloaded += $dest
            } catch {}
        }
    }
    elseif ($api -eq 'mailhog') {
        if (-not $msg.MIME -or -not $msg.MIME.Parts) {
            Add-Content -Path $logFile -Value $id -Encoding utf8
            continue
        }
        $found = $false
        for ($i = 0; $i -lt $msg.MIME.Parts.Count; $i++) {
            $part = $msg.MIME.Parts[$i]
            $disp = $part.Headers.'Content-Disposition'
            if (-not $disp) { continue }
            $d = if ($disp -is [array]) { $disp[0] } else { $disp }
            if ($d -notmatch 'attachment') { continue }
            $found = $true

            $fname = "attachment_$i"
            if ($d -match 'filename="?([^";\s]+)"?') { $fname = $Matches[1] }

            $dest = Join-Path $DownloadDir $fname
            if (Test-Path $dest) { continue }
            try {
                Invoke-WebRequest -Uri "$base/api/v1/messages/$id/mime/part/$i/download" `
                    -OutFile $dest -TimeoutSec 30 -UseBasicParsing
                $downloaded += $dest
            } catch {}
        }
        if (-not $found) {
            Add-Content -Path $logFile -Value $id -Encoding utf8
            continue
        }
    }

    Add-Content -Path $logFile -Value $id -Encoding utf8

    foreach ($f in $downloaded) { Open-Payload $f }

    # One email per Sheepl cycle; the next loop iteration picks up the next.
    break
}
