"""
Product CRUD endpoints
Part C: Endpoints & Behavior
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Product, ProductCreate, ProductUpdate, ProductResponse

router = APIRouter()


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    response_description="The created product",
    responses={
        201: {"description": "Product created successfully"},
        409: {"description": "Product with this SKU already exists"},
        422: {"description": "Validation error"},
    },
)
async def create_product(
    product: ProductCreate,
    session: Session = Depends(get_session)
):
    """
    Create a new product.
    
    - **sku**: Unique product identifier (required, must be unique)
    - **name**: Product name (required)
    - **price**: Product price (required, must be > 0)
    - **stock**: Initial stock level (default: 0, must be >= 0)
    
    Returns 201 on success, 409 if SKU already exists.
    """
    # Check for duplicate SKU
    existing = session.exec(select(Product).where(Product.sku == product.sku)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with SKU '{product.sku}' already exists"
        )
    
    db_product = Product(**product.model_dump())
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product


@router.get(
    "/",
    response_model=List[ProductResponse],
    summary="List all products",
    response_description="List of all products",
)
async def list_products(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """
    Retrieve all products.
    
    - **skip**: Number of products to skip (for pagination)
    - **limit**: Maximum number of products to return (default: 100)
    
    Note: For a tiny store, pagination is optional but included for scalability.
    """
    statement = select(Product).offset(skip).limit(limit)
    products = session.exec(statement).all()
    return products


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get a product by ID",
    response_description="The product details",
    responses={
        200: {"description": "Product found"},
        404: {"description": "Product not found"},
    },
)
async def get_product(
    product_id: int,
    session: Session = Depends(get_session)
):
    """
    Get a single product by ID.
    
    - **product_id**: The ID of the product to retrieve
    
    Returns 404 if product not found.
    """
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    return product


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update a product",
    response_description="The updated product",
    responses={
        200: {"description": "Product updated successfully"},
        404: {"description": "Product not found"},
        409: {"description": "SKU conflict"},
        422: {"description": "Validation error"},
    },
)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    session: Session = Depends(get_session)
):
    """
    Update a product (partial updates allowed).
    
    - **product_id**: The ID of the product to update
    - **sku**: New SKU (optional, must be unique if provided)
    - **name**: New name (optional)
    - **price**: New price (optional, must be > 0)
    - **stock**: New stock level (optional, must be >= 0)
    
    Only provided fields will be updated. Returns 404 if product not found,
    409 if new SKU conflicts with existing product.
    """
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Check for SKU conflict if updating SKU
    if product_update.sku and product_update.sku != db_product.sku:
        existing = session.exec(select(Product).where(Product.sku == product_update.sku)).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{product_update.sku}' already exists"
            )
    
    # Update only provided fields (exclude_unset=True)
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
    responses={
        204: {"description": "Product deleted successfully"},
        404: {"description": "Product not found"},
    },
)
async def delete_product(
    product_id: int,
    session: Session = Depends(get_session)
):
    """
    Delete a product by ID.
    
    - **product_id**: The ID of the product to delete
    
    Returns 204 (No Content) on success, 404 if product not found.
    """
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    session.delete(product)
    session.commit()
    return None
