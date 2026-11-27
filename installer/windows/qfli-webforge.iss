#define RepoRoot AddBackslash(SourcePath) + "..\.."
#define LicensePath AddBackslash(RepoRoot) + "LICENSE"

#ifndef SourceDir
  #error Define SourceDir as the completed Flutter Release directory.
#endif
#ifndef OutputDir
  #error Define OutputDir as the package output directory.
#endif
#ifndef AppVersion
  #error Define AppVersion as the package version.
#endif
#ifndef OutputBaseFilename
  #error Define OutputBaseFilename without the .exe extension.
#endif

[Setup]
AppId={{B7C4E23F-7A91-4C68-9F20-316A8D5E42B1}
AppName=QFLIWebForge
AppVersion={#AppVersion}
AppVerName=QFLIWebForge {#AppVersion}
AppPublisher=AzureKiln
DefaultDirName={userpf}\QFLIWebForge
DefaultGroupName=QFLIWebForge
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
LicenseFile={#LicensePath}
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\qfli_web.exe

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\QFLIWebForge"; Filename: "{app}\qfli_web.exe"; WorkingDir: "{app}"
