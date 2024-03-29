
; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "BehavioralObservation"
#define MyAppVersion "0.4.1.0"
#define MyAppPublisher "EigoNishimura"
#define MyAppURL "https://github.com/nishimura5/VideoObservation"
#define MeventEditorName "MeventEditor.exe"
#define PoseTrackerName "PoseTracker.exe"
#define TrkPlotterName "TrkPlotter.exe"

[Setup]
AppId={{07DDD81D-1966-4E75-B290-81A643754C95}}

AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\BehavioralObservation
ChangesAssociations=yes
DisableProgramGroupPage=yes
LicenseFile=E:\project\VideoObservation\install_license.rtf
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
OutputBaseFilename=BehavioralObservation_installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
SourceDir=E:\project\VideoObservation

[Languages]
;Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}";

[Files]
Source: "MeventEditor\bin\x64\Release\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "PoseTracker\bin\x64\Release\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "TrkPlotter\bin\x64\Release\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "mevent\*"; DestDir: "{app}\mevent"; Excludes: "__pycache__"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "optracker\*"; DestDir: "{app}\optracker"; Excludes: "__pycache__"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "trkproc\*"; DestDir: "{app}\trkproc"; Excludes: "__pycache__"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "python-3.9.7-embed-amd64\*"; DestDir: "{app}\python-3.9.7-embed-amd64"; Excludes: "__pycache__"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
Root: HKA; Subkey: "Software\Classes\Applications\{#MeventEditorName}\SupportedTypes"; ValueType: string; ValueName: ".mevent"; ValueData: ""

[Icons]
Name: "{autoprograms}\{#MeventEditorName}"; Filename: "{app}\{#MeventEditorName}"
Name: "{autoprograms}\{#PoseTrackerName}"; Filename: "{app}\{#PoseTrackerName}"
Name: "{autoprograms}\{#TrkPlotterName}"; Filename: "{app}\{#TrkPlotterName}"
Name: "{autodesktop}\{#MeventEditorName}"; Filename: "{app}\{#MeventEditorName}"; Tasks: desktopicon
Name: "{autodesktop}\{#PoseTrackerName}"; Filename: "{app}\{#PoseTrackerName}"; Tasks: desktopicon
Name: "{autodesktop}\{#TrkPlotterName}"; Filename: "{app}\{#TrkPlotterName}"; Tasks: desktopicon

