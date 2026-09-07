[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$LogDirectory = Join-Path $env:LOCALAPPDATA 'LocalLLMSmartHome'
$LogFile = Join-Path $LogDirectory 'git-autosync.log'
New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null

function Write-Log([string]$Message) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K') [windows] $Message"
    $line | Tee-Object -FilePath $LogFile -Append
}

function Stop-WithError([string]$Message) {
    Write-Log "ERROR: $Message. Local work was preserved."
    exit 1
}

function Stop-Paused([string]$Message) {
    Write-Log "PAUSED: $Message. Inspect git status and resolve deliberately."
    exit 2
}

function Invoke-Git([string[]]$Arguments) {
    & git -C $RepositoryRoot @Arguments
    if ($LASTEXITCODE -ne 0) { throw "git $($Arguments -join ' ') failed" }
}

try {
    & git -C $RepositoryRoot rev-parse --is-inside-work-tree | Out-Null
    if ($LASTEXITCODE -ne 0) { Stop-WithError "Not a Git working tree: $RepositoryRoot" }

    $gitDir = (& git -C $RepositoryRoot rev-parse --git-dir).Trim()
    if (-not [IO.Path]::IsPathRooted($gitDir)) { $gitDir = Join-Path $RepositoryRoot $gitDir }

    foreach ($marker in @('MERGE_HEAD', 'REBASE_HEAD', 'CHERRY_PICK_HEAD', 'index.lock', 'rebase-merge', 'rebase-apply')) {
        if (Test-Path (Join-Path $gitDir $marker)) { Stop-Paused "Git operation marker found: $marker" }
    }

    Write-Log 'Fetching origin/main.'
    Invoke-Git @('fetch', 'origin', '--prune')

    $status = (& git -C $RepositoryRoot status --porcelain)
    if ($status) {
        Invoke-Git @('add', '-A')
        & git -C $RepositoryRoot diff --cached --quiet
        $staged = $LASTEXITCODE
        if ($staged -ne 0) {
            Invoke-Git @('commit', '-m', "autosync(windows): $(Get-Date -Format 'yyyy-MM-dd HH:mm K')")
            Write-Log 'Created a local snapshot commit.'
        }
    }

    & git -C $RepositoryRoot merge-base --is-ancestor origin/main HEAD
    if ($LASTEXITCODE -ne 0) {
        Write-Log 'Rebasing local commits onto origin/main.'
        & git -C $RepositoryRoot rebase origin/main
        if ($LASTEXITCODE -ne 0) { Stop-Paused 'Rebase stopped with a conflict' }
    }

    & git -C $RepositoryRoot merge-base --is-ancestor HEAD origin/main
    if ($LASTEXITCODE -eq 0) {
        Write-Log 'Sync complete; main already matches origin/main.'
        exit 0
    }

    Write-Log 'Pushing main to origin.'
    Invoke-Git @('push', 'origin', 'main')
    Write-Log 'Sync complete.'
}
catch {
    Stop-WithError $_.Exception.Message
}
