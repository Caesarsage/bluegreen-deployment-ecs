import requests
import pytest
import json

BASE_URL_BLUE = "http://localhost:8080"
BASE_URL_GREEN = "http://localhost:8081"

def test_health_check_blue():
    """Test blue environment health"""
    response = requests.get(f"{BASE_URL_BLUE}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['version'] == 'blue'
    assert data['database'] == 'connected'

def test_health_check_green():
    """Test green environment health"""
    response = requests.get(f"{BASE_URL_GREEN}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['version'] == 'green'
    assert data['database'] == 'connected'

def test_create_customer_blue():
    """Test creating customer with V1 API"""
    customer_data = {
        "name": "Test User",
        "email": f"test-blue-{int(time.time())}@example.com",
        "address": "123 Test St, City, ST, 12345"
    }

    response = requests.post(
        f"{BASE_URL_BLUE}/api/customers",
        json=customer_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data['name'] == customer_data['name']
    assert data['address'] == customer_data['address']
    assert 'id' in data

def test_create_customer_green():
    """Test creating customer with V2 API"""
    customer_data = {
        "name": "Test User Green",
        "email": f"test-green-{int(time.time())}@example.com",
        "address": {
            "street": "456 Green Ave",
            "city": "Test City",
            "state": "CA",
            "zip": "90001"
        }
    }

    response = requests.post(
        f"{BASE_URL_GREEN}/api/customers",
        json=customer_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data['name'] == customer_data['name']
    assert data['address']['street'] == customer_data['address']['street']
    assert 'id' in data

def test_list_customers():
    """Test listing customers on both versions"""
    # Blue version
    response_blue = requests.get(f"{BASE_URL_BLUE}/api/customers")
    assert response_blue.status_code == 200

    # Green version
    response_green = requests.get(f"{BASE_URL_GREEN}/api/customers")
    assert response_green.status_code == 200

    # Should have same number of customers
    assert len(response_blue.json()) == len(response_green.json())

def test_backwards_compatibility():
    """Test that green can read data created by blue"""
    import time

    # Create customer with blue (V1)
    customer_data_v1 = {
        "name": "Compatibility Test",
        "email": f"compat-{int(time.time())}@example.com",
        "address": "789 Compat Rd, Test, TX, 75001"
    }

    response = requests.post(
        f"{BASE_URL_BLUE}/api/customers",
        json=customer_data_v1
    )
    customer_id = response.json()['id']

    # Read with green (V2)
    response = requests.get(f"{BASE_URL_GREEN}/api/customers/{customer_id}")
    assert response.status_code == 200

    data = response.json()
    assert data['name'] == customer_data_v1['name']
    assert 'address' in data
    assert 'street' in data['address']
