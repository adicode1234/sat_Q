#!/bin/zsh
# SatQuery AI — Auto-start installer
# Run this once from Terminal to make server start automatically on login

PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.satquery.server.plist"
PROJECT="/Users/adityarajput/Downloads/satquery-ai"

# Create logs directory
mkdir -p "$PROJECT/logs"

# Create the plist
mkdir -p "$PLIST_DIR"
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.satquery.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/zsh</string>
        <string>$PROJECT/start_satquery.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$PROJECT/logs/server.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT/logs/server_error.log</string>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF

# Load it immediately (no restart needed)
launchctl unload "$PLIST_FILE" 2>/dev/null
launchctl load -w "$PLIST_FILE"

echo ""
echo "✅ SatQuery server auto-start installed!"
echo "   Server chal raha hai: http://127.0.0.1:8000"
echo "   Logs: $PROJECT/logs/server.log"
echo "   Band karna ho to: launchctl unload $PLIST_FILE"
