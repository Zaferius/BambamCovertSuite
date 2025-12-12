#define MyAppName        "Bambam Converter Suite"
#define MyAppVersion     "1.2.8"
#define MyAppPublisher   "Bambam Workshop"
#define MyAppExeName     "Bambam Converter Suite.exe"

[Setup]
; Benzersiz GUID – istersen değiştirebilirsin
AppId={{9E5B2CFA-3C0E-4B12-9A1C-7C5A1F8B0D12}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=BambamConverterSuite_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
; Setup ikonun – .ico dosyası exe'nin yanında (dist içinde)
SetupIconFile=dist\bambam_logo.ico

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; dist içindeki her şeyi, klasör yapısıyla birlikte kopyala
; Böylece _internal klasörünün içindeki bambam_logo.png olduğu gibi gider
Source: "dist\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
; Başlat menüsü kısayolu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; Masaüstü kısayolu (isteğe bağlı)
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon

[Run]
; Kurulum bitince programı çalıştırma seçeneği
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchProgram,{#MyAppName}}"; \
    Flags: nowait postinstall skipifsilent
