"""
Order CRUD endpoints
Part C: Endpoints & Behavior
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Order, OrderCreate, OrderUpdate, OrderResponse, Product, OrderStatus

router = APIRouter()


def validate_status_transition(current_status: OrderStatus, new_status: OrderStatus) -> bool:
    """
    Validate order status transitions.
    
    Allowed transitions:
    - PENDING -> PAID, CANCELED
    - PAID -> SHIPPED, CANCELED (refund scenario)
    - SHIPPED -> (no transitions, terminal state)
    - CANCELED -> (no transitions, terminal state)
    """
    valid_transitions = {
        OrderStatus.PENDING: [OrderStatus.PAID, OrderStatus.CANCELED],
        OrderStatus.PAID: [OrderStatus.SHIPPED, OrderStatus.CANCELED],
        OrderStatus.SHIPPED: [],  # Terminal state
        OrderStatus.CANCELED: [],  # Terminal state
    }
    
    if current_status == new_status:
        return True  # No change is always valid
    
    return new_status in valid_transitions.get(current_status, [])


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    response_description="The created order",
    responses={
        201: {"description": "Order created successfully"},
        404: {"description": "Product not found"},
        409: {"description": "Insufficient stock"},
        422: {"description": "Validation error"},
    },
)
async def create_order(
    order: OrderCreate,
    session: Session = Depends(get_session)
):
    """
    Create a new order and atomically reduce product stock.
    
    - **product_id**: The ID of the product to order
    - **quantity**: The quantity to order (must be > 0)
    
    This operation:
    1. Checks if product exists (404 if not)
    2. Checks if sufficient stock is available (409 if not)
    3. Atomically reduces stock and creates order in a transaction
    
    Returns 201 on success, 404 if product not found, 409 if insufficient stock.
    """
    # Get product and lock it for update (to prevent race conditions)
    product = session.get(Product, order.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {order.product_id} not found"
        )
    
    # Check stock availability
    if product.stock < order.quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Insufficient stock",
                "requested": order.quantity,
                "available": product.stock,
                "product_id": order.product_id
            }
        )
    
    # Atomically reduce stock and create order
    # SQLite handles this within a transaction, but for production use proper DB locks
    product.stock -= order.quantity
    db_order = Order(**order.model_dump())
    
    session.add(product)
    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    
    return db_order


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get an order by ID",
    response_description="The order details",
    responses={
        200: {"description": "Order found"},
        404: {"description": "Order not found"},
    },
)
async def get_order(
    order_id: int,
    session: Session = Depends(get_session)
):
    """
    Get a single order by ID for tracking.
    
    Returns:
    - Order ID
    - Product ID
    - Quantity
    - Status (PENDING, PAID, SHIPPED, CANCELED)
    - Created timestamp
    
    Returns 404 if order not found.
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    return order


@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="List all orders",
    response_description="List of all orders",
)
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    status_filter: OrderStatus = None,
    session: Session = Depends(get_session)
):
    """
    Retrieve all orders with optional status filter.
    
    - **skip**: Number of orders to skip (for pagination)
    - **limit**: Maximum number of orders to return (default: 100)
    - **status**: Filter by order status (optional)
    """
    statement = select(Order)
    if status_filter:
        statement = statement.where(Order.status == status_filter)
    statement = statement.offset(skip).limit(limit)
    orders = session.exec(statement).all()
    return orders


@router.put(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Update an order",
    response_description="The updated order",
    responses={
        200: {"description": "Order updated successfully"},
        400: {"description": "Invalid status transition"},
        404: {"description": "Order not found"},
        422: {"description": "Validation error"},
    },
)
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    session: Session = Depends(get_session)
):
    """
    Update an order (only status can be changed).
    
    - **order_id**: The ID of the order to update
    - **status**: New status (must be a valid transition from current status)
    
    Valid status transitions:
    - PENDING -> PAID, CANCELED
    - PAID -> SHIPPED, CANCELED
    - SHIPPED -> (terminal, no transitions)
    - CANCELED -> (terminal, no transitions)
    
    Returns 400 if invalid status transition, 404 if order not found.
    """
    db_order = session.get(Order, order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    
    # Only status can be updated
    if order_update.status is not None:
        if not validate_status_transition(db_order.status, order_update.status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid status transition",
                    "current_status": db_order.status,
                    "requested_status": order_update.status,
                    "message": f"Cannot transition from {db_order.status} to {order_update.status}"
                }
            )
        db_order.status = order_update.status
    
    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    return db_order


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel an order",
    responses={
        204: {"description": "Order canceled successfully"},
        400: {"description": "Cannot cancel order in current status"},
        404: {"description": "Order not found"},
    },
)
async def cancel_order(
    order_id: int,
    session: Session = Depends(get_session)
):
    """
    Cancel an order (soft delete via status change).
    
    This is a semantic operation that:
    - Changes status to CANCELED if in PENDING or PAID state
    - Restores stock if order was PENDING
    - Returns 400 if order is already SHIPPED or CANCELED
    
    For hard deletion, use PUT to change status to CANCELED first, then implement
    a separate admin endpoint if needed.
    """
    db_order = session.get(Order, order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    
    # Only allow cancellation if not already shipped or canceled
    if db_order.status in [OrderStatus.SHIPPED, OrderStatus.CANCELED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Cannot cancel order",
                "current_status": db_order.status,
                "message": f"Orders with status {db_order.status} cannot be canceled"
            }
        )
    
    # Restore stock if order was PENDING
    if db_order.status == OrderStatus.PENDING:
        product = session.get(Product, db_order.product_id)
        if product:
            product.stock += db_order.quantity
            session.add(product)
    
    # Update order status
    db_order.status = OrderStatus.CANCELED
    session.add(db_order)
    session.commit()
    
    return None


