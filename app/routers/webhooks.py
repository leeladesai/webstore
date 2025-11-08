"""
Payment webhook endpoint
Part G: Payment Webhook (Security & E2E)
"""
import hashlib
import hmac
import os
import json
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.requests import Request
from sqlmodel import Session

from app.database import get_session
from app.models import Order, OrderStatus

router = APIRouter()

# Webhook secret from environment variable
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "default-secret-change-in-production")


def verify_hmac_signature(body: bytes, signature: str, secret: str) -> bool:
    """
    Verify HMAC-SHA256 signature of the request body.
    
    Args:
        body: Raw request body bytes
        signature: Expected signature from header
        secret: Shared secret for HMAC
    
    Returns:
        True if signature is valid, False otherwise
    """
    computed_signature = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(computed_signature, signature)


# Store processed event IDs to prevent replay attacks
processed_events: Dict[str, bool] = {}


@router.post(
    "/payment",
    status_code=status.HTTP_200_OK,
    summary="Payment webhook endpoint",
    response_description="Webhook processing result",
    responses={
        200: {"description": "Webhook processed successfully"},
        401: {"description": "Invalid signature"},
        400: {"description": "Invalid request or event already processed"},
        404: {"description": "Order not found"},
    },
)
async def payment_webhook(
    request: Request,
    x_webhook_signature: str = Header(..., alias="X-Webhook-Signature", description="HMAC-SHA256 signature of the request body"),
    x_event_id: str = Header(None, alias="X-Event-Id", description="Unique event ID for replay protection"),
    session: Session = Depends(get_session)
):
    """
    Process payment webhook with HMAC signature verification.
    
    **Security:**
    - Verifies HMAC-SHA256 signature in `X-Webhook-Signature` header
    - Uses `WEBHOOK_SECRET` environment variable for signature computation
    - Prevents replay attacks using `X-Event-Id` header
    
    **Request Headers:**
    - `X-Webhook-Signature`: HMAC-SHA256 signature of the raw request body
    - `X-Event-Id`: Unique event identifier (optional, but recommended for replay protection)
    
    **Request Body (JSON):**
    ```json
    {
        "event": "payment.succeeded",
        "order_id": 123,
        "amount": 99.99,
        "currency": "USD"
    }
    ```
    
    **Behavior:**
    - On `payment.succeeded`: Updates order status to PAID
    - Returns 401 if signature is invalid
    - Returns 400 if event was already processed (replay attack)
    - Returns 404 if order not found
    """
    # Get raw body for signature verification
    body_bytes = await request.body()
    
    # Verify signature
    if not verify_hmac_signature(body_bytes, x_webhook_signature, WEBHOOK_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    # Parse JSON payload
    try:
        payload = json.loads(body_bytes.decode('utf-8'))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {str(e)}"
        )
    
    # Replay protection: Check if event was already processed
    if x_event_id:
        if x_event_id in processed_events:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Event already processed",
                    "event_id": x_event_id,
                    "message": "This event has been processed before (replay attack protection)"
                }
            )
        processed_events[x_event_id] = True
    
    # Process payment event
    event_type = payload.get("event")
    order_id = payload.get("order_id")
    
    if event_type != "payment.succeeded":
        return {
            "status": "ignored",
            "message": f"Event type '{event_type}' is not handled"
        }
    
    if not order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'order_id' in payload"
        )
    
    # Get order
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    
    # Update order status to PAID
    if order.status != OrderStatus.PAID:
        order.status = OrderStatus.PAID
        session.add(order)
        session.commit()
        session.refresh(order)
    
    return {
        "status": "success",
        "message": "Payment processed successfully",
        "order_id": order_id,
        "order_status": order.status
    }

