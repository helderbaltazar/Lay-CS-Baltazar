#!/bin/bash
PLIST_PATH="$HOME/Library/LaunchAgents/com.laycs.scanner.plist"
SCRIPT_DIR=$(pwd)
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"

cat << INNER_EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.laycs.scanner</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$SCRIPT_DIR/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/logs/service.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/logs/service_error.log</string>
</dict>
</plist>
INNER_EOF

echo "Criando pasta de logs..."
mkdir -p "$SCRIPT_DIR/logs"

echo "Servico de background configurado com sucesso!"
echo "Para iniciar rode: launchctl load $PLIST_PATH"
