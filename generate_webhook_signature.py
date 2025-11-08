#!/usr/bin/env python3
"""
Helper script to generate webhook signature for testing
Part G: Payment Webhook (Security & E2E)
"""
import sys
import os
import hmac
import hashlib
import json

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "default-secret-change-in-production")


def generate_signature(body: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature"""
    return hmac.new(
        secret.encode(),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default payload
        payload = {
            "event": "payment.succeeded",
            "order_id": 1,
            "amount": 99.99,
            "currency": "USD"
        }
        body = json.dumps(payload)
    else:
        # Read from file or use as string
        if os.path.exists(sys.argv[1]):
            with open(sys.argv[1], 'r') as f:
                body = f.read()
        else:
            body = sys.argv[1]
    
    signature = generate_signature(body, WEBHOOK_SECRET)
    
    print(f"Body: {body}")
    print(f"Signature: {signature}")
    print(f"\ncurl example:")
    print(f'curl -X POST http://localhost:8000/webhooks/payment \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -H "X-Webhook-Signature: {signature}" \\')
    print(f'  -H "X-Event-Id: $(uuidgen)" \\')
    print(f"  -d '{body}'")

