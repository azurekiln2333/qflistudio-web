param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^[a-z][a-z0-9_-]+$')]
  [string]$NextOwner,
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^[a-zA-Z0-9_-]+$')]
  [string]$RunName,
  [switch]$Worker,
  [switch]$SnapshotOnly
)

# Execute only after a named host grant. This file never claims a slot itself.
# run-web-owned-window.py contains this worker in a suspended-start Windows Job.
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$null = & chcp.com 65001
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$resultPath = Join-Path $PSScriptRoot "$RunName-result.json"
Set-Location -LiteralPath $repoRoot

if ($Worker -or $SnapshotOnly) {
  $result = [ordered]@{
    formatExit = $null
    testExit = $null
    analyzeExit = $null
    exception = $null
    sourceSnapshotsIdentical = $null
    startedUtc = [DateTime]::UtcNow.ToString('o')
    finishedUtc = $null
  }
  $before = $null
  function Read-SourceSnapshot {
    $sources = @(
      Get-ChildItem -LiteralPath (Join-Path $repoRoot 'lib') -Filter '*.dart' -Recurse
      Get-ChildItem -LiteralPath (Join-Path $repoRoot '../qfli_studio_core/lib') -Filter '*.dart' -Recurse
      Get-ChildItem -LiteralPath (Join-Path $repoRoot '../qfli_studio_core/vendor/re_editor/lib') -Filter '*.dart' -Recurse
      Get-Item -LiteralPath (Join-Path $repoRoot '../qfli_studio_core/pubspec.yaml')
      Get-Item -LiteralPath @(
        'pubspec.yaml', 'pubspec.lock', '.dart_tool/package_config.json',
        'analysis_options.yaml',
        'scripts/test_web_console_bridge.mjs', 'scripts/test_web_offline_browser.mjs',
        '.trellis/tasks/10-22-standalone-offline-ide/research/run-web-focused-window.ps1',
        '.trellis/tasks/10-22-standalone-offline-ide/research/run-web-owned-window.py',
        'test/web_dev_server_test.dart', 'test/web_offline_policy_test.dart',
        'test/web_offline_browser_test.dart', 'test/web_server_tools_lifecycle_test.dart',
        'test/web_code_analyzer_test.dart', 'test/web_saved_workspaces_test.dart'
      )
      if ($env:QFLI_WEB_SYNTAX_LIBRARY) {
        Get-Item -LiteralPath $env:QFLI_WEB_SYNTAX_LIBRARY
      } elseif (Test-Path -LiteralPath 'build/native/web_syntax/windows/qfli_web_syntax.dll') {
        Get-Item -LiteralPath 'build/native/web_syntax/windows/qfli_web_syntax.dll'
      }
    )
    return @($sources | Sort-Object FullName -Unique | ForEach-Object {
      $hasher = [Security.Cryptography.SHA256]::Create()
      $stream = [IO.File]::OpenRead($_.FullName)
      try {
        $hash = [BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-', '')
        [ordered]@{ path = $_.FullName; sha256 = $hash }
      } finally {
        $stream.Dispose()
        $hasher.Dispose()
      }
    }) | ConvertTo-Json -Depth 4
  }
  if ($SnapshotOnly) {
    $snapshot = Read-SourceSnapshot | ConvertFrom-Json
    Write-Output "Snapshot verified: $($snapshot.Count) files; no formatter/test/analyzer started."
    exit 0
  }
  try {
    $flutterPath = (Get-Command flutter).Source
    $dartPath = Join-Path (Split-Path $flutterPath) 'cache/dart-sdk/bin/dart.exe'
    $files = @(
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
    # Windows PowerShell wraps native stderr as error records even on exit 0.
    # Capture the real exit code; do not let a warning skip result publication.
    $ErrorActionPreference = 'Continue'
    & $dartPath format @files 2>&1 |
      Tee-Object -FilePath (Join-Path $PSScriptRoot "$RunName-format.log")
    $result.formatExit = $LASTEXITCODE
    if ($result.formatExit -ne 0) { throw 'Scoped formatter failed' }
    $ErrorActionPreference = 'Stop'
    $before = Read-SourceSnapshot
    $before | Set-Content -LiteralPath (Join-Path $PSScriptRoot "$RunName-source-before.json") -Encoding UTF8
    $ErrorActionPreference = 'Continue'
    & $flutterPath test --no-pub --concurrency=1 --timeout 35s `
      test/web_dev_server_test.dart test/web_offline_policy_test.dart `
      test/web_offline_browser_test.dart test/web_code_analyzer_test.dart `
      test/web_saved_workspaces_test.dart test/web_server_tools_lifecycle_test.dart `
      --reporter expanded 2>&1 |
      Tee-Object -FilePath (Join-Path $PSScriptRoot "$RunName-tests.log")
    $result.testExit = $LASTEXITCODE
    # Analysis remains useful after an ordinary test failure, within the same bound.
    & $flutterPath analyze --no-pub @files 2>&1 |
      Tee-Object -FilePath (Join-Path $PSScriptRoot "$RunName-analysis.log")
    $result.analyzeExit = $LASTEXITCODE
  } catch {
    $result.exception = $_.Exception.Message
  } finally {
    $ErrorActionPreference = 'Stop'
    if ($null -ne $before) {
      $after = Read-SourceSnapshot
      $after | Set-Content -LiteralPath (Join-Path $PSScriptRoot "$RunName-source-after.json") -Encoding UTF8
      $result.sourceSnapshotsIdentical = $before -ceq $after
      if (-not $result.sourceSnapshotsIdentical) {
        $result.exception = 'Source snapshot changed during checks; results are not a frozen checkpoint'
      }
    }
    $result.finishedUtc = [DateTime]::UtcNow.ToString('o')
    $result | ConvertTo-Json -Depth 4 |
      Set-Content -LiteralPath $resultPath -Encoding UTF8
  }
  if ($result.formatExit -eq 0 -and $result.testExit -eq 0 -and
      $result.analyzeExit -eq 0 -and $null -eq $result.exception) { exit 0 }
  exit 1
}

throw "Launch through run-web-owned-window.py so the worker and all descendants belong to an owned Windows Job."
