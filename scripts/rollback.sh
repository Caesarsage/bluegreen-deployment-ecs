#!/bin/bash
set -e

echo "=== EMERGENCY ROLLBACK ==="
echo "This will switch ALL traffic back to BLUE environment"
read -p "Are you sure? (type 'rollback' to confirm): " CONFIRM

if [ "$CONFIRM" != "rollback" ]; then
    echo "Rollback cancelled."
    exit 1
fi

cd terraform

ALB_ARN=$(terraform output -raw alb_arn)
BLUE_TG_ARN=$(terraform output -raw blue_target_group_arn)
LISTENER_ARN=$(terraform output -raw alb_listener_arn)

echo "Switching traffic to blue target group..."

aws elbv2 modify-listener \
    --listener-arn $LISTENER_ARN \
    --default-actions Type=forward,TargetGroupArn=$BLUE_TG_ARN \
    --region ${AWS_REGION:-us-east-1}

echo "✅ Rollback complete! All traffic now on BLUE."
echo "Monitor: aws elbv2 describe-target-health --target-group-arn $BLUE_TG_ARN"
