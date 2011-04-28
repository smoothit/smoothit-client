
IF "%~1"=="" GOTO :Usage
copy vlc.pyd %1
copy libvlc.dll %1
copy libvlccore.dll %1
xcopy *.* %1\vlc /S
GOTO :EOF

:Usage
ECHO Usage: arno-install.bat targetdir
