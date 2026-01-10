#!/usr/bin/env python3
"""
Synthetic monitoring script for blue-green deployments
Run this continuously to monitor both environments
"""

import requests
import time
import json
from datetime import datetime

BLUE_URL = "http://localhost:8080"
GREEN_URL = "http://localhost:8081"

def check_environment(name, base_url):
    """Check health and basic functionality of an environment"""
    results = {
        'environment': name,
        'timestamp': datetime.now().isoformat(),
        'health': False,
        'api_list': False,
        'response_time_ms': 0
    }

    try:
        # Health check
        start = time.time()
        response = requests.get(f"{base_url}/health", timeout=5)
        results['response_time_ms'] = int((time.time() - start) * 1000)
        results['health'] = response.status_code == 200

        # API test
        response = requests.get(f"{base_url}/api/customers", timeout=5)
        results['api_list'] = response.status_code == 200

    except Exception as e:
        results['error'] = str(e)

    return results

def run_synthetic_tests():
    """Run synthetic tests against both environments"""
    print(f"\n{'='*60}")
    print(f"Synthetic Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    blue_results = check_environment('BLUE', BLUE_URL)
    green_results = check_environment('GREEN', GREEN_URL)

    # Print results
    for results in [blue_results, green_results]:
        status = "✅" if results['health'] and results['api_list'] else "❌"
        print(f"\n{status} {results['environment']}")
        print(f"   Health: {results['health']}")
        print(f"   API: {results['api_list']}")
        print(f"   Response Time: {results['response_time_ms']}ms")
        if 'error' in results:
            print(f"   Error: {results['error']}")

    return blue_results, green_results

if __name__ == '__main__':
    print("Starting Synthetic Monitor...")
    print("Press Ctrl+C to stop")

    try:
        while True:
            run_synthetic_tests()
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
