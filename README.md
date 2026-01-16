
# Blue-Green Deployment with ECS - Complete Implementation

Production-ready example of blue-green deployment handling database migrations using the expand-contract pattern.

## Article Link
I have also written a more detailed article about this project on freecodecamp. Click the link below to read more:

[How to manage blue green deployment on aws ecs with database migrations](https://www.freecodecamp.org/news/how-to-manage-blue-green-deployments-on-aws-ecs-with-database-migrations/
)

## Quick Start (Local Testing)

### 1. Prerequisites
```bash
# Required
- Docker & Docker Compose
- Python 3.11+
- Make (optional, but recommended)

# For AWS deployment
- AWS CLI configured
- Terraform 1.0+
```


### 2. Setup Local Environment

**Local (No Docker):**
```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r app/requirements.txt
psql postgres -c "CREATE DATABASE ecommerce;"
psql -U postgres -d ecommerce -f docker/init.sql

# Terminal 1 - Blue
export $(cat .env.blue | xargs)
cd app && python main.py

# Terminal 2 - Green
export $(cat .env.green | xargs) && export PORT=8081
cd app && python main.py

# Terminal 3 - Test
curl http://localhost:8080/health
curl http://localhost:8081/health
```

**Local (Docker):**

```bash
# Clone and enter directory
cd ecs-bluegreen-demo

# Install dependencies
make setup

# Start both environments
make start
```

This starts:
- **Blue environment** (V1) on http://localhost:8080
- **Green environment** (V2) on http://localhost:8081
- **PostgreSQL** database on localhost:5432

### 3. Test the Initial State

```bash
# Check both environments are healthy
curl http://localhost:8080/health
curl http://localhost:8081/health

# List customers (both should return same data)
curl http://localhost:8080/api/customers
curl http://localhost:8081/api/customers

# Create customer with V1 API (Blue)
curl -X POST http://localhost:8080/api/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "address": "123 Main St, New York, NY, 10001"
  }'

# Create customer with V2 API (Green) - will fail without migration
curl -X POST http://localhost:8081/api/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane.smith@example.com",
    "address": {
      "street": "456 Oak Ave",
      "city": "Los Angeles",
      "state": "CA",
      "zip": "90001"
    }
  }'
```

### 4. Run Expand Migration

```bash
# Copy migration file into container
docker cp migrations/001_expand_address.sql \
  $(docker-compose -f docker/docker-compose.yml ps -q db):/tmp/

# Run migration
docker-compose -f docker/docker-compose.yml exec db \
  psql -U postgres -d ecommerce -f /tmp/001_expand_address.sql

# Or use make command
make migrate-expand
```

### 5. Test Both Versions Working Together

```bash
# Now green can create customers with structured address
curl -X POST http://localhost:8081/api/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane.smith@example.com",
    "address": {
      "street": "456 Oak Ave",
      "city": "Los Angeles",
      "state": "CA",
      "zip": "90001"
    }
  }'

# Blue still works with old format
curl -X POST http://localhost:8080/api/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bob Johnson",
    "email": "bob.j@example.com",
    "address": "789 Pine Rd, Chicago, IL, 60601"
  }'

# Both can read all customers
curl http://localhost:8080/api/customers | jq
curl http://localhost:8081/api/customers | jq
```

### 6. Run Automated Tests

```bash
# Run full test suite
make test

# Or manually
pytest tests/test_api.py -v
```

### 7. Monitor Both Environments

```bash
# Run continuous monitoring
make monitor

# This will check every 30 seconds:
# - Health status
# - API functionality
# - Response times
```

### 8. Simulate Traffic Switch

In production, CodeDeploy would gradually shift traffic. Locally, you can simulate by:

```bash
# Use a load balancer like nginx or just switch your client calls
# From: http://localhost:8080 (blue)
# To:   http://localhost:8081 (green)

# Or use a simple Python script to distribute requests
python -c "
import requests
import random

for i in range(100):
    url = random.choice([
        'http://localhost:8080/api/customers',
        'http://localhost:8081/api/customers'
    ])
    r = requests.get(url)
    print(f'Request {i}: {url} -> {r.status_code}')
"
```

### 9. Contract Phase (After Green is Stable)

```bash
# WARNING: This removes the old 'address' column
# Only do this after:
# - Green has been stable for 24-72 hours
# - All traffic has moved to green
# - Blue environment is decommissioned

make migrate-contract

# Now blue will break if you try to use it
# This is expected - blue is retired
```

## Testing Scenarios

### Scenario 1: Backwards Compatibility
```bash
# 1. Create customer with Blue (old format)
CUSTOMER_ID=$(curl -s -X POST http://localhost:8080/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","address":"123 St, City, ST, 12345"}' \
  | jq -r '.id')

# 2. Read with Green (should parse into structured format)
curl http://localhost:8081/api/customers/$CUSTOMER_ID | jq
```

### Scenario 2: Forward Compatibility
```bash
# 1. Create with Green (structured format)
CUSTOMER_ID=$(curl -s -X POST http://localhost:8081/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"Test2","email":"test2@test.com","address":{"street":"456 Ave","city":"Town","state":"CA","zip":"90001"}}' \
  | jq -r '.id')

# 2. Read with Blue (should have combined address)
curl http://localhost:8080/api/customers/$CUSTOMER_ID | jq
```

### Scenario 3: Rollback
```bash
# At any point before contract phase, you can "rollback" by:
# 1. Stop sending traffic to green
# 2. Continue using blue
# 3. The database still works for both

# Simulate rollback
echo "Switching all traffic back to blue..."
# In production: scripts/rollback.sh
```

## Monitoring & Debugging

```bash
# View logs
make logs-blue
make logs-green

# Check database
docker-compose -f docker/docker-compose.yml exec db \
  psql -U postgres -d ecommerce -c "\d customers"

# Check which columns exist
docker-compose -f docker/docker-compose.yml exec db \
  psql -U postgres -d ecommerce -c \
  "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='customers';"
```

## Cleanup

```bash
# Stop and remove all containers
make clean

# Or keep data and just stop
docker-compose -f docker/docker-compose.yml stop
```

## AWS Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for full AWS deployment with Terraform.

## Troubleshooting

**Green fails health check after starting:**
- Run the expand migration first
- Check logs: `make logs-green`

**"Column does not exist" errors:**
- Verify migration ran: `docker-compose exec db psql -U postgres -d ecommerce -c "\d customers"`

**Both environments return same format:**
- Check APP_VERSION environment variable
- Rebuild containers: `make rebuild`
```

---

## How to Test - Complete Guide

### Local Testing (Recommended First)

1. **Start everything:**
```bash
make start
```

2. **Verify initial state:**
```bash
# Both should be healthy
curl http://localhost:8080/health | jq
curl http://localhost:8081/health | jq
```

3. **Test Blue (before migration):**
```bash
curl -X POST http://localhost:8080/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"Blue Test","email":"blue@test.com","address":"123 St, City, ST, 12345"}'
```

4. **Test Green fails (before migration):**
```bash
# This should fail because structured fields don't exist yet
curl -X POST http://localhost:8081/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"Green Test","email":"green@test.com","address":{"street":"456 Ave","city":"Town","state":"CA","zip":"90001"}}'
```

5. **Run expand migration:**
```bash
make migrate-expand
```

6. **Now both work:**
```bash
# Blue still works
curl -X POST http://localhost:8080/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"Blue Test 2","email":"blue2@test.com","address":"789 Rd, Place, ST, 67890"}'

# Green now works too!
curl -X POST http://localhost:8081/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"Green Test","email":"green@test.com","address":{"street":"456 Ave","city":"Town","state":"CA","zip":"90001"}}'
```

7. **Run automated tests:**
```bash
make test
```

8. **Monitor continuously:**
```bash
make monitor
# Press Ctrl+C to stop
```
