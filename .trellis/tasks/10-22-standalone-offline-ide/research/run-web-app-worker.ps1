param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('format', 'tests', 'analysis', 'content')]
  [string]$Phase,
  [Parameter(Mandatory = $true)]
  [string]$EvidenceDirectory,
  [Parameter(Mandatory = $true)]
  [string]$FlutterExecutable,
  [Parameter(Mandatory = $true)]
  [string]$PythonExecutable,
  [switch]$OwnedWorker
)

# Fixed commands only. The Python supervisor owns deadlines and every child.
if (-not $OwnedWorker) {
  throw 'Launch through run-web-app-window.py after a new named host grant.'
}
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$null = & chcp.com 65001
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$evidenceRoot = [IO.Path]::GetFullPath($EvidenceDirectory)
$allowedRoot = [IO.Path]::GetFullPath($PSScriptRoot) + [IO.Path]::DirectorySeparatorChar
if (-not $evidenceRoot.StartsWith($allowedRoot, [StringComparison]::OrdinalIgnoreCase) -or
    -not (Test-Path -LiteralPath $evidenceRoot -PathType Container)) {
  throw 'Evidence directory must be a fresh existing child of this task research directory.'
}
Set-Location -LiteralPath $repoRoot

try {
  # Supervisor supplies single literal Application paths; never look them up again.
  if (-not [IO.Path]::IsPathRooted($FlutterExecutable) -or
      -not [IO.File]::Exists($FlutterExecutable) -or
      [IO.Path]::GetFileName($FlutterExecutable) -ine 'flutter.bat') {
    throw 'One absolute existing Flutter batch executable is required.'
  }
  if (-not [IO.Path]::IsPathRooted($PythonExecutable) -or
      -not [IO.File]::Exists($PythonExecutable) -or
      [IO.Path]::GetExtension($PythonExecutable) -ine '.exe' -or
      (($PythonExecutable -split '[\\/]') -icontains 'WindowsApps')) {
    throw 'One absolute existing Python executable is required; WindowsApps aliases are refused.'
  }
  [string]$flutterPath = (Get-Item -LiteralPath $FlutterExecutable -ErrorAction Stop).FullName
  [string]$pythonPath = (Get-Item -LiteralPath $PythonExecutable -ErrorAction Stop).FullName
  $dartPath = Join-Path (Split-Path $flutterPath) 'cache/dart-sdk/bin/dart.exe'
  if ($Phase -eq 'format' -and -not (Test-Path -LiteralPath $dartPath -PathType Leaf)) {
    throw 'Installed Dart formatter executable missing.'
  }
  Write-Output ('ResolvedApplicationPaths: ' + (@{
    flutter = $flutterPath
    dart = $dartPath
    python = $pythonPath
  } | ConvertTo-Json -Compress))
  $ownedFiles = @(
    'lib/services/web_dev_server.dart',
    'lib/services/web_project_config.dart',
    'lib/services/nginx_session.dart',
    'lib/services/web_code_analyzer.dart',
    'lib/pages/web_tools_page.dart',
    'test/web_dev_server_test.dart',
    'test/web_offline_policy_test.dart',
    'test/web_offline_browser_test.dart',
    'test/web_server_tools_lifecycle_test.dart',
    'test/web_code_analyzer_test.dart',
    'test/web_saved_workspaces_test.dart'
  )
  # Native stderr is an ErrorRecord in Windows PowerShell. Preserve native exit.
  $ErrorActionPreference = 'Continue'
  $global:LASTEXITCODE = $null
  switch ($Phase) {
    'format' {
      & $dartPath format --output=none --set-exit-if-changed @ownedFiles
    }
    'tests' {
      & $flutterPath test --no-pub --concurrency=1 --timeout 35s --reporter expanded
    }
    'analysis' {
      & $flutterPath analyze --no-pub lib test integration_test tool
    }
    'content' {
      & $pythonPath -X utf8 scripts/audit_web_content.py --product `
        --report (Join-Path $evidenceRoot 'content-audit.md')
    }
  }
  $phaseExit = $LASTEXITCODE
  if ($null -eq $phaseExit) { throw 'Native command returned no exit code.' }
  exit $phaseExit
} catch {
  [Console]::Error.WriteLine($_.Exception.ToString())
  exit 1
}
