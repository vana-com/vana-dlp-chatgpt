#!/bin/bash

# TODO: move this process to an external Vana-only location

# Create the directory for the startup script, if it doesn't already exist
mkdir -p /opt/startup

# Write the service script itself
cat << 'EOF' > /opt/startup/startup.sh
#!/bin/bash
get_metadata() {
  curl -s -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/$1"
}

# Retrieve the metadata values using the function
PROJECT=$(get_metadata "attributes/project")
IMAGE=$(get_metadata "attributes/image")
INSTANCE_NAME=$(get_metadata "name")
ZONE=$(get_metadata "zone" | awk -F/ '{print $NF}')
ENV_BASE64=$(get_metadata "attributes/env_base64")

# Obtain external IP address via gcloud command
while [ -z "$EXTERNAL_IP" ]; do
  EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
    --zone="$ZONE" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

  if [ -z "$EXTERNAL_IP" ]; then
    echo "Waiting for external IP address... ($INSTANCE_NAME, $ZONE)"
    sleep 2
  fi
done

if ! command -v docker &> /dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
fi

# Stop and remove existing Docker container
docker stop validator || true
docker rm validator || true

# Pull and run the Docker container
docker pull "$IMAGE"

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
EOF

# Make the script executable
chmod +x /opt/startup/startup.sh

# Write the systemd service file
cat << 'EOF' > /etc/systemd/system/startup.service
[Unit]
Description=Run startup script to set up Docker container on boot
After=network.target

[Service]
Type=oneshot
ExecStart=/opt/startup/startup.sh

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to recognize the new service and enable/start it
systemctl daemon-reload
systemctl enable startup.service
systemctl start startup.service
