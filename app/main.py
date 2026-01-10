from flask import Flask, request, jsonify

from flask_cors import CORS
from models import Customer, db
from config import config
import logging
import boto3
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# CloudWatch client for custom metrics
try:
    cloudwatch = boto3.client('cloudwatch', region_name=config.AWS_REGION)
except:
    cloudwatch = None
    logger.warning("CloudWatch client not available")

def emit_metric(metric_name, value, unit='Count'):
    """Emit custom CloudWatch metric"""
    if cloudwatch:
        try:
            cloudwatch.put_metric_data(
                Namespace='EcommerceApp',
                MetricData=[{
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Dimensions': [
                        {'Name': 'Environment', 'Value': config.APP_VERSION},
                        {'Name': 'Stage', 'Value': config.ENVIRONMENT}
                    ]
                }]
            )
        except Exception as e:
            logger.error(f"Failed to emit metric: {e}")

@app.route('/health')
def health_check():
    """Health check endpoint"""
    checks = {
        'status': 'healthy',
        'version': config.APP_VERSION,
        'environment': config.ENVIRONMENT,
        'database': 'unknown',
        'schema': 'unknown'
    }

    try:
        # Check database connection
        db.query("SELECT 1")
        checks['database'] = 'connected'

        # Check schema compatibility
        if config.APP_VERSION == 'blue':
            # V1 only needs address column
            result = db.query_one("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'customers' AND column_name = 'address'
            """)
            checks['schema'] = 'compatible' if result else 'incompatible'
        else:
            # V2 needs structured fields
            result = db.query("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'customers'
                AND column_name IN ('street_address', 'city', 'state', 'zip_code')
            """)
            checks['schema'] = 'compatible' if len(result) == 4 else 'incompatible'

        status_code = 200 if checks['database'] == 'connected' and checks['schema'] == 'compatible' else 503
        return jsonify(checks), status_code

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        checks['status'] = 'unhealthy'
        checks['error'] = str(e)
        return jsonify(checks), 503

@app.route('/')
def index():
    """API information"""
    return jsonify({
        'service': 'E-commerce API',
        'version': config.APP_VERSION,
        'environment': config.ENVIRONMENT,
        'endpoints': {
            'health': '/health',
            'customers': {
                'list': 'GET /api/customers',
                'get': 'GET /api/customers/:id',
                'create': 'POST /api/customers',
                'update': 'PUT /api/customers/:id'
            }
        }
    })

@app.route('/api/customers', methods=['GET'])
def list_customers():
    """List all customers"""
    try:
        customers = Customer.all()
        emit_metric('CustomersListed', len(customers))
        return jsonify([c.to_dict() for c in customers])
    except Exception as e:
        logger.error(f"Failed to list customers: {e}")
        emit_metric('CustomerListError', 1)
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers/', methods=['GET'])
def get_customer(customer_id):
    """Get customer by ID"""
    try:
        customer = Customer.find(customer_id)
        if customer:
            emit_metric('CustomerRetrieved', 1)
            return jsonify(customer.to_dict())
        else:
            return jsonify({'error': 'Customer not found'}), 404
    except Exception as e:
        logger.error(f"Failed to get customer: {e}")
        emit_metric('CustomerRetrieveError', 1)
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers', methods=['POST'])
def create_customer():
    """Create new customer"""
    try:
        data = request.get_json()

        if config.APP_VERSION == 'blue':
            # V1 API expects single address field
            customer = Customer(
                name=data.get('name'),
                email=data.get('email'),
                address=data.get('address')
            )
        else:
            # V2 API expects structured address
            address = data.get('address', {})
            customer = Customer(
                name=data.get('name'),
                email=data.get('email'),
                street_address=address.get('street'),
                city=address.get('city'),
                state=address.get('state'),
                zip_code=address.get('zip')
            )

        customer.save()
        emit_metric('CustomerCreated', 1)

        return jsonify(customer.to_dict()), 201

    except Exception as e:
        logger.error(f"Failed to create customer: {e}")
        emit_metric('CustomerCreateError', 1)
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers/', methods=['PUT'])
def update_customer(customer_id):
    """Update customer"""
    try:
        customer = Customer.find(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        data = request.get_json()

        if config.APP_VERSION == 'blue':
            customer.name = data.get('name', customer.name)
            customer.email = data.get('email', customer.email)
            customer.address = data.get('address', customer.address)
        else:
            address = data.get('address', {})
            customer.name = data.get('name', customer.name)
            customer.email = data.get('email', customer.email)
            customer.street_address = address.get('street', customer.street_address)
            customer.city = address.get('city', customer.city)
            customer.state = address.get('state', customer.state)
            customer.zip_code = address.get('zip', customer.zip_code)

        customer.save()
        emit_metric('CustomerUpdated', 1)

        return jsonify(customer.to_dict())

    except Exception as e:
        logger.error(f"Failed to update customer: {e}")
        emit_metric('CustomerUpdateError', 1)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=(config.ENVIRONMENT == 'development'))
