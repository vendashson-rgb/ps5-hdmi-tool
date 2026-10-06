; Instalador do PS5 HDMI Tool.
; Gera um unico .exe que instala o programa + o driver do leitor CH341A
; automaticamente (via pnputil, builtin do Windows) -- o usuario so clica
; "Avancar/Instalar", sem precisar abrir o Gerenciador de Dispositivos na mao.
;
; Nao precisa instalar Python na maquina do usuario: o PS5_HDMI_Tool.exe foi
; gerado com PyInstaller --onefile e ja carrega o Python embutido.
;
; Driver do controle DualSense: nao precisa de driver separado -- Windows ja
; tem suporte nativo a dispositivos HID USB (teclado/mouse/controle), entao
; nao ha nada pra instalar alem do proprio programa.
;
; Build: "C:\Users\O Honorio\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer.iss

#define MyAppName "PS5 HDMI Tool"
#define MyAppVersion "1.0.16"
#define MyAppExeName "PS5_HDMI_Tool.exe"
#define MyAppPublisher "DatZero Foundation"
#define MyAppURL "https://datzerogames.com.br/"

[Setup]
AppId={{7B6C9B6A-6B1A-4C3E-9C2D-PS5HDMITOOL01}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; Estes tres viram os campos "Publicador/Link de suporte/Link de Ajuda" que o
; Windows mostra pro programa instalado (busca do menu Iniciar, Configuracoes
; > Aplicativos) -- mesmo painel que aparece pra programas como o Python.
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) 2026 {#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=PS5_HDMI_Tool_Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
SetupIconFile=images\icon.ico
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
; Informacoes do proprio arquivo Setup.exe (aba Detalhes nas Propriedades dele).
VersionInfoVersion=1.0.16.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Instalador do {#MyAppName}
VersionInfoProductName={#MyAppName}
VersionInfoCopyright=Copyright (C) 2026 {#MyAppPublisher}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
; Build "onedir" (pasta, nao .exe unico) -- copia a pasta inteira gerada
; pelo PyInstaller. Isso faz o programa abrir muito mais rapido, porque um
; .exe unico ("onefile") tem que se descompactar numa pasta temporaria
; toda vez que abre; em pasta, ele roda direto, sem esse passo.
Source: "dist\PS5_HDMI_Tool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "drives\*"; DestDir: "{app}\drives"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
; Instala o driver do leitor CH341A direto no sistema (driver store do
; Windows), usando o pnputil que ja vem com o Windows -- assim, quando o
; usuario conectar o leitor, o Windows reconhece sozinho, sem pedir pra
; apontar a pasta do driver na mao.
; {sysnative} (nao {sys}) e necessario aqui: o instalador e 32 bits, e em
; Windows 64 bits o {sys} de um processo 32 bits e redirecionado pelo WOW64
; pra SysWOW64 -- onde pnputil.exe NAO existe (so existe no System32 de 64
; bits de verdade). {sysnative} fura esse redirecionamento; em Windows de
; 32 bits ele automaticamente equivale a {sys} (documentado pelo Inno Setup).
Filename: "{sysnative}\pnputil.exe"; Parameters: "/add-driver ""{app}\drives\CH341WDM.INF"" /install"; StatusMsg: "Instalando driver do leitor CH341A..."; Flags: runhidden waituntilterminated

Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remove o driver do sistema ao desinstalar (nao afeta outros programas que
; usem o mesmo chip CH341A instalados separadamente, so limpa essa entrada).
Filename: "{sysnative}\pnputil.exe"; Parameters: "/delete-driver CH341WDM.INF /uninstall /force"; RunOnceId: "RemoveCH341Driver"; Flags: runhidden
