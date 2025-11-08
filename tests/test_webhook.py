"""
Webhook testing script
Part G: Payment Webhook (Security & E2E)
"""
import os
import requests
import json
import hmac
import hashlib
import uuid

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "default-secret-change-in-production")


def generate_signature(body: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for webhook body"""
    return hmac.new(
        secret.encode(),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def test_webhook_valid_signature():
    """Test webhook with valid signature"""
    print("\n1. Testing webhook with VALID signature...")
    
    # First, create a product and order
    product_data = {"sku": "WEBHOOK-001", "name": "Webhook Test Product", "price": 50.0, "stock": 10}
    product_resp = requests.post(f"{BASE_URL}/products/", json=product_data)
    product_id = product_resp.json()["id"]
    
    order_data = {"product_id": product_id, "quantity": 2}
    order_resp = requests.post(f"{BASE_URL}/orders/", json=order_data)
    order_id = order_resp.json()["id"]
    
    # Prepare webhook payload
    payload = {
        "event": "payment.succeeded",
        "order_id": order_id,
        "amount": 100.0,
        "currency": "USD"
    }
    body = json.dumps(payload)
    signature = generate_signature(body, WEBHOOK_SECRET)
    event_id = str(uuid.uuid4())
    
    # Send webhook request
    headers = {
        "X-Webhook-Signature": signature,
        "X-Event-Id": event_id,
        "Content-Type": "application/json"
    }
    response = requests.post(f"{BASE_URL}/webhooks/payment", data=body, headers=headers)
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json()["status"] == "success"
    
    # Verify order status changed to PAID
    order_check = requests.get(f"{BASE_URL}/orders/{order_id}")
    assert order_check.json()["status"] == "PAID"
    print(f"   ✅ Order status changed to PAID")
    
    return event_id


def test_webhook_invalid_signature():
    """Test webhook with invalid signature"""
    print("\n2. Testing webhook with INVALID signature...")
    
    payload = {
        "event": "payment.succeeded",
        "order_id": 1,
        "amount": 100.0
    }
    body = json.dumps(payload)
    # Use wrong secret to generate signature
    signature = generate_signature(body, "wrong-secret")
    event_id = str(uuid.uuid4())
    
    headers = {
        "X-Webhook-Signature": signature,
        "X-Event-Id": event_id,
        "Content-Type": "application/json"
    }
    response = requests.post(f"{BASE_URL}/webhooks/payment", data=body, headers=headers)
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print(f"   ✅ Correctly rejected invalid signature")


def test_webhook_replay_attack():
    """Test webhook replay attack protection"""
    print("\n3. Testing replay attack protection...")
    
    # First create a valid event
    product_data = {"sku": "REPLAY-001", "name": "Replay Test", "price": 25.0, "stock": 5}
    product_resp = requests.post(f"{BASE_URL}/products/", json=product_data)
    product_id = product_resp.json()["id"]
    
    order_data = {"product_id": product_id, "quantity": 1}
    order_resp = requests.post(f"{BASE_URL}/orders/", json=order_data)
    order_id = order_resp.json()["id"]
    
    payload = {
        "event": "payment.succeeded",
        "order_id": order_id,
        "amount": 25.0
    }
    body = json.dumps(payload)
    signature = generate_signature(body, WEBHOOK_SECRET)
    event_id = str(uuid.uuid4())
    
    headers = {
        "X-Webhook-Signature": signature,
        "X-Event-Id": event_id,
        "Content-Type": "application/json"
    }
    
    # First request should succeed
    response1 = requests.post(f"{BASE_URL}/webhooks/payment", data=body, headers=headers)
    assert response1.status_code == 200
    
    # Second request with same event_id should be rejected
    response2 = requests.post(f"{BASE_URL}/webhooks/payment", data=body, headers=headers)
    print(f"   First request status: {response1.status_code}")
    print(f"   Second request status: {response2.status_code}")
    print(f"   Second response: {response2.json()}")
    
    assert response2.status_code == 400, f"Expected 400 for replay, got {response2.status_code}"
    print(f"   ✅ Replay attack correctly prevented")


if __name__ == "__main__":
    print(f"Testing webhooks against: {BASE_URL}")
    test_webhook_valid_signature()
    test_webhook_invalid_signature()
    test_webhook_replay_attack()
    print("\n✅ All webhook tests passed!")


