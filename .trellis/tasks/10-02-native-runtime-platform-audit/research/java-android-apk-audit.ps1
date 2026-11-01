param(
    [Parameter(Mandatory)][string]$Apk,
    [Parameter(Mandatory)][string]$PackageRoot,
    [Parameter(Mandatory)][string]$EvidenceDirectory,
    [string]$Ndk = 'D:/ProgramData/Android/Sdk/ndk/27.0.12077973'
)

$ErrorActionPreference = 'Stop'
$Apk = (Resolve-Path -LiteralPath $Apk).ProviderPath
$PackageRoot = (Resolve-Path -LiteralPath $PackageRoot).ProviderPath
New-Item -ItemType Directory -Force -Path $EvidenceDirectory | Out-Null
$EvidenceDirectory = (Resolve-Path -LiteralPath $EvidenceDirectory).ProviderPath
$archive = [IO.Compression.ZipFile]::OpenRead($Apk)
$strip = Join-Path $Ndk 'toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-strip.exe'
$reports = @()

function Get-EntryHash($Entry) {
    $stream = $Entry.Open()
    try {
        return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream)).ToLowerInvariant()
    } finally { $stream.Dispose() }
}

try {
    $unexpected = @($archive.Entries | Where-Object {
        $_.FullName -like 'lib/*' -and $_.Length -gt 0 -and
        $_.FullName -notmatch '^lib/(arm64-v8a|x86_64)/[^/]+\.so$'
    })
    if ($unexpected.Count) { throw "Unexpected native APK entries: $($unexpected.FullName -join ', ')" }
    foreach ($abi in @('arm64-v8a', 'x86_64')) {
        $expectedRoot = Join-Path $PackageRoot "jniLibs/$abi"
        $expectedFiles = @(Get-ChildItem -LiteralPath $expectedRoot -Filter '*.so' -File)
        $runtimeRoot = Join-Path $EvidenceDirectory "runtime/$abi"
        $frameworkRoot = Join-Path $EvidenceDirectory "framework/$abi"
        $packagedExpectedRoot = Join-Path $EvidenceDirectory "expected-packaged/$abi"
        New-Item -ItemType Directory -Force -Path $runtimeRoot, $frameworkRoot, $packagedExpectedRoot | Out-Null
        $sourceInputs = @(
            foreach ($file in $expectedFiles) {
                $destination = Join-Path $packagedExpectedRoot $file.Name
                # Match Android Gradle's strip step and the owning keepDebugSymbols rule.
                $kept = $file.Name -like 'libqfli_*.so'
                if ($kept) {
                    Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
                } else {
                    & $strip --strip-unneeded -o $destination $file.FullName
                    if ($LASTEXITCODE -ne 0) { throw "Strip failed: $($file.FullName)" }
                }
                [ordered]@{
                    file = $file.Name
                    stagedSha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                    packagedSha256 = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
                    transformation = if ($kept) { 'keepDebugSymbols' } else { 'llvm-strip --strip-unneeded' }
                }
            }
        )
        $entries = @($archive.Entries | Where-Object { $_.FullName -like "lib/$abi/*" -and $_.Length -gt 0 })
        foreach ($entry in $entries) {
            $root = if ($entry.Name -in $expectedFiles.Name) { $runtimeRoot } else { $frameworkRoot }
            if ($root -eq $frameworkRoot -and $entry.Name -notin @('libflutter.so', 'libVkLayer_khronos_validation.so')) {
                throw "Unexpected framework library: $($entry.FullName)"
            }
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, (Join-Path $root $entry.Name), $true)
        }
        & (Join-Path $PSScriptRoot 'java-android-elf-audit.ps1') -InputRoot $runtimeRoot -Mode package -Abi $abi `
            -ExpectedRoot $packagedExpectedRoot -ExpectedMode package -Ndk $Ndk `
            -Output (Join-Path $EvidenceDirectory "runtime-$abi.json")
        & (Join-Path $PSScriptRoot 'java-android-elf-audit.ps1') -InputRoot $frameworkRoot -Mode package -Abi $abi `
            -Ndk $Ndk -Output (Join-Path $EvidenceDirectory "framework-$abi.json")
        $data = @(
            foreach ($extension in @('json', 'zip')) {
                $relative = "assets/jdk-$abi.$extension"
                $entry = $archive.GetEntry($relative)
                if (-not $entry) { throw "Missing JDK asset: $relative" }
                $hash = Get-EntryHash $entry
                $expectedHash = (Get-FileHash -LiteralPath (Join-Path $PackageRoot $relative) -Algorithm SHA256).Hash.ToLowerInvariant()
                if ($hash -ne $expectedHash) { throw "JDK asset hash mismatch: $relative" }
                [ordered]@{ file = $relative; sha256 = $hash; matchesExpected = $true }
            }
        )
        $reports += [ordered]@{
            abi = $abi
            runtimeNativeCount = $expectedFiles.Count
            frameworkNativeCount = @($entries | Where-Object { $_.Name -notin $expectedFiles.Name }).Count
            sourceInputs = $sourceInputs
            assets = $data
        }
    }
} finally { $archive.Dispose() }

$report = [ordered]@{
    apk = $Apk
    sha256 = (Get-FileHash -LiteralPath $Apk -Algorithm SHA256).Hash.ToLowerInvariant()
    size = (Get-Item -LiteralPath $Apk).Length
    valid = $true
    abis = $reports
}
[IO.File]::WriteAllText((Join-Path $EvidenceDirectory 'apk-audit.json'), ($report | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
Write-Output "PASS: both APK JDK native packages match the owning staged inputs after the exact Gradle strip step; both data archives match directly. SHA-256 $($report.sha256)"
