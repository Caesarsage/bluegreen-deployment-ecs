#!/bin/bash
set -e

ENVIRONMENT=${1:-blue}
IMAGE_TAG=${2:-latest}

if [ "$ENVIRONMENT" != "blue" ] && [ "$ENVIRONMENT" != "green" ]; then
    echo "Usage: ./deploy.sh  [image-tag]"
    exit 1
fi

echo "Deploying $ENVIRONMENT environment with image tag: $IMAGE_TAG"

# Update ECS service with new image
cd terraform

# Get service name
SERVICE_NAME=$(terraform output -raw ecs_service_${ENVIRONMENT}_name)
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)

echo "Updating ECS service: $SERVICE_NAME in cluster: $CLUSTER_NAME"

# Force new deployment
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --force-new-deployment \
    --region ${AWS_REGION:-us-east-1}

echo "Deployment initiated. Monitor progress:"
echo "aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME"
