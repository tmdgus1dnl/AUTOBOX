#!/bin/bash
# AutoBox MQTT Password Generator
set -e
PASSWD_FILE="$(dirname "$0")/passwd"

echo "AutoBox MQTT Password Generator"
if ! command -v docker > /dev/null; then
    echo "Error: Docker required"
    exit 1
fi

echo "# AutoBox MQTT Password File" > "$PASSWD_FILE"
for user in backend raspberry-pi dashboard; do
    echo "Enter password for '$user':"
    read -s password
    docker run -it --rm eclipse-mosquitto:2 mosquitto_passwd -b -c /dev/stdout "$user" "$password" >> "$PASSWD_FILE"
    echo "Added: $user"
done
echo "Done! Restart: docker-compose restart mosquitto"
