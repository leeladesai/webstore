"""
FastAPI Orders & Inventory Microservice
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, init_db
from app.routers import products, orders, webhooks

# Initialize database
init_db()

# Create FastAPI app with OpenAPI metadata
app = FastAPI(
    title="Orders & Inventory Microservice",
    version="1.0.0",
    description="""
    A microservice for managing products and orders in an online store.
    
    ## Features
    
    * **Products**: CRUD operations for product inventory
    * **Orders**: Create and manage orders with automatic stock reduction
    * **Webhooks**: Payment webhook endpoint with HMAC signature verification
    
    ## Endpoints
    
    * `/products` - Product management
    * `/orders` - Order management
    * `/webhooks/payment` - Payment webhook handler
    """,
    tags_metadata=[
        {
            "name": "products",
            "description": "Operations with products. Create, read, update, and delete products in the inventory.",
        },
        {
            "name": "orders",
            "description": "Operations with orders. Create orders, track status, and manage order lifecycle.",
        },
        {
            "name": "webhooks",
            "description": "Webhook endpoints for external integrations, including payment processing.",
        },
    ],
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Orders & Inventory Microservice API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


