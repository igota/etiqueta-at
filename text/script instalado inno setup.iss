[Setup]
AppName=EtiquetaAT
AppVersion=1.0
DefaultDirName={pf}\EtiquetaAT
OutputBaseFilename=EtiquetaAT
Compression=lzma
SolidCompression=yes

[Files]
Source: "C:\Projeto Etiqueta Ag Transfusional\dist\run.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Projeto Etiqueta Ag Transfusional\tools\nssm.exe"; DestDir: "{app}\tools"; Flags: ignoreversion

[Run]
Filename: "{app}\tools\nssm.exe"; Parameters: "install EtiquetaAT ""{app}\run.exe"""; Flags: runhidden