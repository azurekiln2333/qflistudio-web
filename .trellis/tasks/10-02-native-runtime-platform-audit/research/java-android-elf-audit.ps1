param(
    [Parameter(Mandatory)][string]$InputRoot,
    [Parameter(Mandatory)][ValidateSet('image', 'package')][string]$Mode,
    [Parameter(Mandatory)][ValidateSet('arm64-v8a', 'x86_64')][string]$Abi,
    [Parameter(Mandatory)][string]$Output,
    [string]$ExpectedRoot,
    [ValidateSet('image', 'package')][string]$ExpectedMode = 'image',
    [string]$Ndk = 'D:/ProgramData/Android/Sdk/ndk/27.0.12077973'
)

$ErrorActionPreference = 'Stop'
$InputRoot = (Resolve-Path -LiteralPath $InputRoot).ProviderPath
$prebuilt = Join-Path $Ndk 'toolchains/llvm/prebuilt/windows-x86_64'
$reader = Join-Path $prebuilt 'bin/llvm-readobj.exe'
$triple = if ($Abi -eq 'arm64-v8a') { 'aarch64-linux-android' } else { 'x86_64-linux-android' }
$machine = if ($Abi -eq 'arm64-v8a') { 183 } else { 62 }
$systemLibraries = @(Get-ChildItem -LiteralPath (Join-Path $prebuilt "sysroot/usr/lib/$triple/28") -Filter '*.so' -File | ForEach-Object Name)

function Get-NativeFiles([string]$Root) {
    foreach ($file in Get-ChildItem -LiteralPath $Root -File -Recurse) {
        if ($file.Name -like '*.debuginfo') { continue }
        $stream = $file.OpenRead()
        try {
            $magic = [byte[]]::new(4)
            $length = $stream.Read($magic, 0, 4)
        } finally { $stream.Dispose() }
        if ($length -eq 4 -and $magic[0] -eq 127 -and $magic[1] -eq 69 -and
            $magic[2] -eq 76 -and $magic[3] -eq 70) { $file }
    }
}

function Get-PackageName([string]$Relative) {
    switch ($Relative) {
        'bin/java' { return 'libqfli_java.so' }
        'bin/javac' { return 'libqfli_javac.so' }
        'lib/jexec' { return 'libqfli_jexec.so' }
        'lib/jspawnhelper' { return 'libqfli_jspawnhelper.so' }
        default {
            if ($Relative -match '\.so(?:\.[0-9]+)*$') {
                return ([IO.Path]::GetFileName($Relative) -replace '\.so(?:\.[0-9]+)+$', '.so')
            }
        }
    }
}

$files = @(Get-NativeFiles $InputRoot | Sort-Object FullName)
if ($files.Count -eq 0) { throw "No native files in $InputRoot" }
$arguments = @('--elf-output-style=JSON', '--file-header', '--program-headers', '--needed-libs') + @($files.FullName)
$raw = & $reader @arguments
if ($LASTEXITCODE -ne 0) { throw 'LLVM native inspection failed.' }
$objects = @($raw -join "`n" | ConvertFrom-Json)
if ($objects.Count -ne $files.Count) { throw 'LLVM inspection omitted an input.' }
$bundled = @($objects | ForEach-Object {
    [IO.Path]::GetFileName($_.FileSummary.File)
    if ($_.FileSummary.LoadName -ne '<Not found>') { $_.FileSummary.LoadName }
})

$expected = @{}
if ($ExpectedRoot) {
    $ExpectedRoot = (Resolve-Path -LiteralPath $ExpectedRoot).ProviderPath
    foreach ($file in Get-NativeFiles $ExpectedRoot) {
        $relative = [IO.Path]::GetRelativePath($ExpectedRoot, $file.FullName).Replace('\', '/')
        $name = if ($ExpectedMode -eq 'image') { Get-PackageName $relative } else { $relative }
        if (-not $name) { continue }
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($expected.ContainsKey($name) -and $expected[$name] -ne $hash) {
            throw "Conflicting expected native input: $name"
        }
        $expected[$name] = $hash
    }
}

$entries = @(
    foreach ($object in $objects) {
        $path = $object.FileSummary.File
        $relative = [IO.Path]::GetRelativePath($InputRoot, $path).Replace('\', '/')
        $loads = @($object.ProgramHeaders | ForEach-Object ProgramHeader | Where-Object { $_.Type.Value -eq 1 })
        $invalidLoads = @($loads | Where-Object {
            $_.Alignment -lt 16384 -or $_.Offset % 16384 -ne $_.VirtualAddress % 16384
        })
        $needed = @($object.NeededLibraries)
        $missing = @($needed | Where-Object { $_ -notin $bundled -and $_ -notin $systemLibraries })
        $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        $expectedHash = if ($expected.ContainsKey($relative)) { $expected[$relative] } else { $null }
        $matches = -not $ExpectedRoot -or ($expectedHash -and $expectedHash -eq $hash)
        [ordered]@{
            file = $relative
            machine = $object.ElfHeader.Machine.Name
            sha256 = $hash
            loads = @($loads | ForEach-Object {
                [ordered]@{ alignment = $_.Alignment; offset = $_.Offset; address = $_.VirtualAddress }
            })
            dependencies = $needed
            missing = $missing
            expectedSha256 = $expectedHash
            matchesExpected = [bool]$matches
            valid = ($object.ElfHeader.Machine.Value -eq $machine -and
                $object.ElfHeader.Ident.Class.Value -eq 2 -and
                $object.ElfHeader.Ident.DataEncoding.Value -eq 1 -and
                $loads.Count -gt 0 -and $invalidLoads.Count -eq 0 -and
                $missing.Count -eq 0 -and $matches)
        }
    }
)
$omitted = @($expected.Keys | Where-Object { $_ -notin $entries.file })
$failures = @($entries | Where-Object { -not $_.valid })
$report = [ordered]@{
    abi = $Abi
    mode = $Mode
    inputRoot = $InputRoot
    minimumAndroidApi = 28
    pageSize = 16384
    nativeCount = $entries.Count
    expectedCount = $expected.Count
    omitted = $omitted
    valid = ($failures.Count -eq 0 -and $omitted.Count -eq 0)
    files = $entries
}
[IO.File]::WriteAllText([IO.Path]::GetFullPath($Output), ($report | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
if (-not $report.valid) {
    throw "Native audit failed: $($failures.file -join ', '); omitted: $($omitted -join ', ')"
}
Write-Output "PASS $Abi $Mode`: $($entries.Count) ELF files; 16 KiB LOAD/dependencies/hashes verified."
