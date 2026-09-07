param(
    [Parameter(Mandatory=$true)][string]$ArtifactManifest,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$taskManifest = Get-Content -LiteralPath $ArtifactManifest -Raw | ConvertFrom-Json
$taskOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $taskOutput -Force | Out-Null
$taskWord = New-Object -ComObject Word.Application
$taskWord.Visible = $false
$taskWord.DisplayAlerts = 0
$taskWord.AutomationSecurity = 3
$taskReceipts = @()
try {
    foreach ($taskName in @('manuscript','proposal')) {
        $taskItem = $taskManifest.exports.$taskName
        $taskHash = (Get-FileHash -LiteralPath $taskItem.path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($taskHash -ne $taskItem.sha256) { throw 'Artifact differs from the selected manifest' }
        $taskDocument = $taskWord.Documents.Open($taskItem.path,$false,$true)
        try {
            $taskPdf = Join-Path $taskOutput ($taskName + '.pdf')
            $taskDocument.ExportAsFixedFormat($taskPdf,17)
            $taskReceipts += [pscustomobject]@{ name=$taskName; source=$taskItem.path; sha256=$taskHash; renderer='Word'; version=$taskWord.Version; pdf=$taskPdf }
        } finally { $taskDocument.Close(0) }
    }
} finally { $taskWord.Quit() }
$taskPowerPoint = New-Object -ComObject PowerPoint.Application
$taskPowerPoint.AutomationSecurity = 3
try {
    $taskItem = $taskManifest.exports.deck
    $taskHash = (Get-FileHash -LiteralPath $taskItem.path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($taskHash -ne $taskItem.sha256) { throw 'Deck differs from the selected manifest' }
    $taskDeck = $taskPowerPoint.Presentations.Open($taskItem.path,-1,0,0)
    try {
        $taskSlides = Join-Path $taskOutput 'slides'
        New-Item -ItemType Directory -Path $taskSlides -Force | Out-Null
        $taskDeck.Export($taskSlides,'PNG',1600,900)
        $taskReceipts += [pscustomobject]@{ name='deck'; source=$taskItem.path; sha256=$taskHash; renderer='PowerPoint'; version=$taskPowerPoint.Version; slides=$taskDeck.Slides.Count; output=$taskSlides }
    } finally { $taskDeck.Close() }
} finally { $taskPowerPoint.Quit() }
$taskReceipts | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskOutput 'render-receipt.json') -Encoding utf8
$taskReceipts | ConvertTo-Json -Depth 5
