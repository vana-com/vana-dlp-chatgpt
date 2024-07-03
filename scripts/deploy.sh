#!/bin/bash

# TODO: move this process to an external Vana-only location

# Typically you will want to run it like this: ./scripts/deploy.sh -d prd_satori -t stable or ./scripts/deploy.sh -d prd_satori.
# This will create NUM_NODES VM instances in the specified PROJECT with IMAGE:stable or IMAGE:latest using the prd_satori Doppler project.

source "$(dirname "$0")/env.sh"

DEFAULT_NAMESPACE=satori-hotdog

PROJECT=${PROJECT:-corsali-production}
NUM_NODES=${NUM_NODES:-1}
MACHINE_TYPE=${MACHINE_TYPE:-n1-standard-1}
IMAGE=${IMAGE:-vanaorg/dlp-hotdog-validator}
ZONE=${ZONE:-us-central1-a}
DOPPLER_PROJECT=${DOPPLER_PROJECT:-prd}
TAG=${TAG:-latest}
RESTART="false"

parse_args() {
    while getopts "p:n:m:i:z:d:a:t:r:h" opt; do
        case $opt in
            p) PROJECT=$OPTARG ;;
            n) NUM_NODES=$OPTARG ;;
            m) MACHINE_TYPE=$OPTARG ;;
            i) IMAGE=$OPTARG ;;
            z) ZONE=$OPTARG ;;
            d) DOPPLER_PROJECT=$OPTARG ;;
            a) NAMESPACE=$OPTARG ;;
            t) TAG=$OPTARG ;;
            r) RESTART=true ;;
            h) echo "Usage: $0 [-p project] [-n num_nodes] [-m machine_type] [-i image] [-z zone] [-d doppler_project] [-a namespace] [-r restart] "; exit ;;
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

# Loop through node creation or update
for ((i=1; i<=NUM_NODES; i++)); do
  VM_NAME="${NAMESPACE}-validator-$i"

  # Check if the instance exists
  if gcloud compute instances describe "$VM_NAME" --project="$PROJECT" --zone="$ZONE" > /dev/null 2>&1; then
    # Update metadata and startup script for the existing instance
    gcloud compute instances add-metadata "$VM_NAME" \
      --project="$PROJECT" \
      --zone="$ZONE" \
      --metadata project="$PROJECT",image="$IMAGE_TAG",env_base64="$ENV_BASE64" \
      --metadata-from-file startup-script=scripts/startup.sh
      # If the flag is set, restart the VM to apply the changes
      if [ "$RESTART" = "true" ]; then
        gcloud compute instances stop "$VM_NAME" --project="$PROJECT" --zone="$ZONE"
        gcloud compute instances start "$VM_NAME" --project="$PROJECT" --zone="$ZONE"
      fi
    echo "Updated VM instance $VM_NAME"
  else
    # Create the VM instance if it doesn't exist
    gcloud compute instances create "$VM_NAME" \
      --project="$PROJECT" \
      --zone="$ZONE" \
      --machine-type="$MACHINE_TYPE" \
      --image-family="ubuntu-2004-lts" \
      --image-project="ubuntu-os-cloud" \
      --tags="allow-tcp-5555" \
      --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/compute.readonly \
      --metadata project="$PROJECT",image="$IMAGE_TAG",env_base64="$ENV_BASE64" \
      --metadata-from-file startup-script=scripts/startup.sh

    echo "Created VM instance $VM_NAME"
  fi
done
