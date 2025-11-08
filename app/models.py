"""
Data models for Product and Order
Part B: Data Modeling & Validation
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enum"""
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELED = "CANCELED"


class Product(SQLModel, table=True):
    """
    Product model with validation constraints
    
    Constraints:
    - sku: unique identifier for product
    - price: must be > 0
    - stock: must be >= 0
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(unique=True, index=True, description="Unique product SKU")
    name: str = Field(description="Product name")
    price: float = Field(gt=0, description="Product price (must be > 0)")
    stock: int = Field(ge=0, default=0, description="Available stock (must be >= 0)")
    
    # Indexes: sku is already indexed (unique=True), add index on name for search
    # SQLModel/SQLAlchemy will create indexes automatically for unique fields
    
    class Config:
        schema_extra = {
            "example": {
                "sku": "PROD-001",
                "name": "Laptop",
                "price": 999.99,
                "stock": 50
            }
        }


class Order(SQLModel, table=True):
    """
    Order model with validation
    
    Constraints:
    - quantity: must be > 0
    - status: constrained to OrderStatus enum values
    - created_at: auto-generated timestamp
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id", index=True, description="Product ID")
    quantity: int = Field(gt=0, description="Order quantity (must be > 0)")
    status: OrderStatus = Field(default=OrderStatus.PENDING, index=True, description="Order status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Order creation timestamp")
    
    # Indexes: product_id and status are indexed for fast lookups and filtering
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": 1,
                "quantity": 2,
                "status": "PENDING"
            }
        }


# Pydantic models for request/response
class ProductCreate(SQLModel):
    """Product creation request model"""
    sku: str
    name: str
    price: float
    stock: int = 0


class ProductUpdate(SQLModel):
    """Product update request model (partial updates allowed)"""
    sku: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None


class ProductResponse(SQLModel):
    """Product response model"""
    id: int
    sku: str
    name: str
    price: float
    stock: int


class OrderCreate(SQLModel):
    """Order creation request model"""
    product_id: int
    quantity: int


class OrderUpdate(SQLModel):
    """Order update request model"""
    status: Optional[OrderStatus] = None


class OrderResponse(SQLModel):
    """Order response model"""
    id: int
    product_id: int
    quantity: int
    status: OrderStatus
    created_at: datetime


