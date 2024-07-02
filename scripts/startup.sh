#!/bin/bash

# TODO: move this process to an external Vana-only location

# Create the directory for the validator script, if it doesn't already exist
mkdir -p /opt/validator

# Write the service script itself
cat << 'EOF' > /opt/validator/validator.sh
#!/bin/bash

LOGFILE="/var/log/validator_update.log"

log() {
  echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" >> "$LOGFILE"
}

log "Validator script started."

get_metadata() {
  curl -s -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/$1"
}

pull_and_get_latest_image_digest() {
  docker pull "$1" > /dev/null 2>&1
  docker inspect --format='{{.RepoDigests}}' "$1" | sed 's/[^[]*\[\([^]]*\)\].*/\1/'
}

check_update_and_restart() {
  NEW_IMAGE=$(get_metadata "attributes/image")
  NEW_ENV_BASE64=$(get_metadata "attributes/env_base64")
  NEW_IMAGE_DIGEST=$(pull_and_get_latest_image_digest "$NEW_IMAGE")

  if [[ "$NEW_IMAGE" != "$IMAGE" ]] || [[ "$NEW_ENV_BASE64" != "$ENV_BASE64" ]] || [[ "$NEW_IMAGE_DIGEST" != "$IMAGE_DIGEST" ]]; then
    log "Detected change in image, environment variables, or image digest, updating container..."
    IMAGE="$NEW_IMAGE"
    ENV_BASE64="$NEW_ENV_BASE64"
    IMAGE_DIGEST="$NEW_IMAGE_DIGEST"
    restart_container
  fi
}

restart_container() {
  log "Stopping current Docker container..."
  docker stop validator || true
  docker rm validator || true
  docker system prune -a -f > /dev/null 2>&1
  log "Pulling new Docker image..."
  docker pull "$IMAGE"
  log "Starting new Docker container..."
  docker run -d --name validator \
    $(echo "$ENV_BASE64" | base64 --decode | sed 's/^/-e /' | sed 's/$/ /' | tr -d '\n') \
    -e OD_NODESERVER_EXTERNAL_IP="$EXTERNAL_IP" \
    -e OD_NODESERVER_EXTERNAL_PORT=5555 \
    -e OD_NODESERVER_PORT=5555 \
    -p 5555:5555 \
    -v /root/.vana:/root/.vana \
    --log-driver=gcplogs \
    --log-opt gcp-project="$PROJECT" \
    "$IMAGE"
}

# Retrieve the metadata values using the function
PROJECT=$(get_metadata "attributes/project")
IMAGE=$(get_metadata "attributes/image")
INSTANCE_NAME=$(get_metadata "name")
ZONE=$(get_metadata "zone" | awk -F/ '{print $NF}')
ENV_BASE64=$(get_metadata "attributes/env_base64")

# Initial Docker setup
if ! command -v docker &> /dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
fi

IMAGE_DIGEST=$(pull_and_get_latest_image_digest "$IMAGE")

# Obtain External IP and Initial Startup
while [ -z "$EXTERNAL_IP" ]; do
  EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
    --zone="$ZONE" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

  if [ -z "$EXTERNAL_IP" ]; then
    echo "Waiting for external IP address... ($INSTANCE_NAME, $ZONE)"
    sleep 2
  fi
done
restart_container

# Poll for updates every 1 minute
while true; do
  check_update_and_restart
  sleep 60
done
EOF

# Make the script executable
chmod +x /opt/validator/validator.sh

# Write the systemd service file
cat << 'EOF' > /etc/systemd/system/validator.service
[Unit]
Description=Manage Validator Docker Container
After=network.target

[Service]
Type=simple
ExecStart=/opt/validator/validator.sh
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to recognize the new service and enable/start it
systemctl daemon-reload
systemctl enable validator.service
systemctl start validator.service
