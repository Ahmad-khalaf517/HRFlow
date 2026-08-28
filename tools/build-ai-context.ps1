[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TaskFile,

    [string[]]$IncludeFiles = @(),

    [string]$OutputPath = (Join-Path ([System.IO.Path]::GetTempPath()) 'hrp-ai-context-bundle.md'),

    [switch]$ConfirmSanitized,

    [switch]$Overwrite
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $ConfirmSanitized) {
    throw 'Review every requested file under docs/security-and-data-policy.md, then rerun with -ConfirmSanitized.'
}

$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\', '/')
$repositoryBoundary = $repositoryRoot + [System.IO.Path]::DirectorySeparatorChar

$blockedFileNames = @(
    '.env',
    'id_rsa',
    'id_ed25519',
    'credentials.json',
    'secrets.json'
)

$blockedExtensions = @(
    '.pem', '.key', '.pfx', '.p12',
    '.sqlite', '.sqlite3', '.db', '.dump', '.bak',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.png', '.jpg', '.jpeg', '.gif', '.zip', '.7z'
)

$secretPatterns = @(
    '(?im)^\s*(SECRET_KEY|API_KEY|ACCESS_TOKEN|REFRESH_TOKEN|PASSWORD|DATABASE_URL)\s*=\s*\S+',
    '-----BEGIN [A-Z ]*PRIVATE KEY-----',
    '(?i)\b(sk|pk)_[a-z0-9_-]{20,}\b'
)

function Resolve-RepositoryFile {
    param([Parameter(Mandatory = $true)][string]$RequestedPath)

    $candidate = if ([System.IO.Path]::IsPathRooted($RequestedPath)) {
        [System.IO.Path]::GetFullPath($RequestedPath)
    }
    else {
        [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot $RequestedPath))
    }

    if (($candidate -ne $repositoryRoot) -and (-not $candidate.StartsWith($repositoryBoundary, [System.StringComparison]::OrdinalIgnoreCase))) {
        throw "Path is outside the repository: $RequestedPath"
    }

    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "File does not exist: $RequestedPath"
    }

    $item = Get-Item -LiteralPath $candidate
    if ($blockedFileNames -contains $item.Name.ToLowerInvariant()) {
        throw "Blocked sensitive filename: $RequestedPath"
    }

    if ($blockedExtensions -contains $item.Extension.ToLowerInvariant()) {
        throw "Blocked binary or sensitive file type: $RequestedPath"
    }

    return $item
}

$requestedFiles = @('AI_CONTEXT.md', $TaskFile) + $IncludeFiles
$resolvedFiles = @()
$seenPaths = @{}

foreach ($requestedFile in $requestedFiles) {
    $item = Resolve-RepositoryFile -RequestedPath $requestedFile
    if (-not $seenPaths.ContainsKey($item.FullName)) {
        $seenPaths[$item.FullName] = $true
        $resolvedFiles += $item
    }
}

$sections = New-Object System.Collections.Generic.List[string]

foreach ($item in $resolvedFiles) {
    $fileContent = Get-Content -LiteralPath $item.FullName -Raw

    foreach ($pattern in $secretPatterns) {
        if ($fileContent -match $pattern) {
            throw "Possible secret detected in $($item.FullName). Remove or sanitize it before creating a bundle."
        }
    }

    $relativePath = [System.IO.Path]::GetRelativePath($repositoryRoot, $item.FullName).Replace('\', '/')
    $section = @"
## Source: $relativePath

~~~text
$fileContent
~~~
"@
    $sections.Add($section)
}

$commit = 'unknown'
try {
    $commit = (& git -C $repositoryRoot rev-parse HEAD 2>$null).Trim()
}
catch {
    $commit = 'unknown'
}

$header = @"
# HRP AI Context Bundle

> Generated for a bounded task. Review this entire file before uploading it anywhere.
> The builder blocks common secret file types and patterns but cannot reliably detect personal, payroll, or confidential data.

- Repository commit: $commit
- Generated UTC: $([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))
- Task source: $TaskFile

"@

$bundle = $header + ($sections -join "`n")
$absoluteOutputPath = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $absoluteOutputPath

if ((Test-Path -LiteralPath $absoluteOutputPath) -and (-not $Overwrite)) {
    throw "Output already exists: $absoluteOutputPath. Use -Overwrite only after confirming the target."
}

if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}

[System.IO.File]::WriteAllText($absoluteOutputPath, $bundle, [System.Text.UTF8Encoding]::new($false))

Write-Output "Created: $absoluteOutputPath"
Write-Output "Included files: $($resolvedFiles.Count)"
Write-Output 'Required next step: manually review the generated bundle before uploading it to an approved AI service.'
