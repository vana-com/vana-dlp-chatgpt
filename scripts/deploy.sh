#!/bin/bash

# TODO: move this process to an external Vana-only location

# Typically you will want to run it like this: ./scripts/deploy.sh -d prd_satori -t stable or ./scripts/deploy.sh -d prd_satori.
# This will create NUM_NODES VM instances in the specified PROJECT with IMAGE:stable or IMAGE:latest using the prd_satori Doppler project.

source "$(dirname "$0")/env.sh"

DEFAULT_NAMESPACE=default

PROJECT=${PROJECT:-corsali-production}
NUM_NODES=${NUM_NODES:-3}
MACHINE_TYPE=${MACHINE_TYPE:-n1-standard-1}
IMAGE=${IMAGE:-timvana/dlp-chatgpt-validator}
ZONE=${ZONE:-us-central1-a}
DOPPLER_PROJECT=${DOPPLER_PROJECT:-prd}
TAG=${TAG:-latest}

parse_args() {
    while getopts "p:n:m:i:z:d:a:t:h" opt; do
        case $opt in
            p) PROJECT=$OPTARG ;;
            n) NUM_NODES=$OPTARG ;;
            m) MACHINE_TYPE=$OPTARG ;;
            i) IMAGE=$OPTARG ;;
            z) ZONE=$OPTARG ;;
            d) DOPPLER_PROJECT=$OPTARG ;;
            a) NAMESPACE=$OPTARG ;;
            t) TAG=$OPTARG ;;
            h) echo "Usage: $0 [-p project] [-n num_nodes] [-m machine_type] [-i image] [-z zone] [-d doppler_project] [-a namespace]"; exit ;;
            \?) echo "Invalid option: -$OPTARG. Use -h for help." >&2; exit 1 ;;
        esac
    done
}
parse_args "$@"

if [ -z "$NAMESPACE" ]; then
    NAMESPACE=$(doppler secrets get REDIS_PERSONAL_NS --project dlp-chatgpt-validator --config $DOPPLER_PROJECT --plain 2>/dev/null || echo $DEFAULT_NAMESPACE)
fi

IMAGE_TAG="${IMAGE}:${TAG:-latest}"

TEMP_DOPPLER_ENV=$(mktemp)
doppler secrets download --project dlp-chatgpt-validator --config "$DOPPLER_PROJECT" --no-file --format docker > "$TEMP_DOPPLER_ENV"
ENV_BASE64=$(base64 -w 0 "$TEMP_DOPPLER_ENV" 2>/dev/null || base64 -i "$TEMP_DOPPLER_ENV")
rm -f "$TEMP_DOPPLER_ENV"

# Ensure firewall rule is in place
if ! gcloud compute firewall-rules list --project="$PROJECT" --filter="name=allow-tcp-5555" --format="value(name)" | grep -q allow-tcp-5555; then
  gcloud compute firewall-rules create allow-tcp-5555 \
   --project="$PROJECT" \
   --allow tcp:5555 \
   --source-ranges=0.0.0.0/0 \
   --target-tags="allow-tcp-5555" > /dev/null 2>&1
fi

echo "Using image: $IMAGE_TAG"

# Loop through node creation
for ((i=1; i<=NUM_NODES; i++)); do
  VM_NAME="${NAMESPACE}-chatgpt-validator-$i"

  # Create the VM instance
  gcloud compute instances create "$VM_NAME" \
    --project="$PROJECT" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --image-family="ubuntu-2004-lts" \
    --image-project="ubuntu-os-cloud" \
    --tags="allow-tcp-5555" \
    --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/compute.readonly \
    --metadata-from-file startup-script=scripts/startup.sh \
    --metadata project="$PROJECT",image="$IMAGE_TAG",env_base64="$ENV_BASE64"
done
