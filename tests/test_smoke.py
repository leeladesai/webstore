"""
Smoke tests for the API
Part F: Black-Box Testing (Python)
"""
import os
import requests
import json

# Base URL from environment variable or default to local
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def test_create_product_and_order():
    """
    Creates a product and an order, asserts status codes, and prints the final order JSON.
    """
    print(f"Testing against: {BASE_URL}")
    
    # Create a product
    print("\n1. Creating a product...")
    product_data = {
        "sku": "TEST-001",
        "name": "Test Product",
        "price": 29.99,
        "stock": 100
    }
    response = requests.post(f"{BASE_URL}/products/", json=product_data)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    product = response.json()
    print(f"   Product created: {product}")
    product_id = product["id"]
    
    # Create an order
    print("\n2. Creating an order...")
    order_data = {
        "product_id": product_id,
        "quantity": 5
    }
    response = requests.post(f"{BASE_URL}/orders/", json=order_data)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    order = response.json()
    print(f"   Order created: {order}")
    order_id = order["id"]
    
    # Get the order
    print("\n3. Getting the order...")
    response = requests.get(f"{BASE_URL}/orders/{order_id}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    final_order = response.json()
    print(f"\n   Final Order JSON:")
    print(json.dumps(final_order, indent=2, default=str))
    
    # Verify stock was reduced
    print("\n4. Verifying stock was reduced...")
    response = requests.get(f"{BASE_URL}/products/{product_id}")
    assert response.status_code == 200
    updated_product = response.json()
    assert updated_product["stock"] == 95, f"Expected stock 95, got {updated_product['stock']}"
    print(f"   Stock updated correctly: {updated_product['stock']}")
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_create_product_and_order()


