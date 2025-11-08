#!/bin/bash
# Part F: Black-Box Testing (curl)
# Example curl commands for testing the API

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "Testing API at: $BASE_URL"
echo ""

# 1. Create a product
echo "1. Creating a product..."
PRODUCT_RESPONSE=$(curl -s -X POST "$BASE_URL/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "CURL-001",
    "name": "Curl Test Product",
    "price": 49.99,
    "stock": 50
  }')
echo "$PRODUCT_RESPONSE" | python3 -m json.tool
PRODUCT_ID=$(echo "$PRODUCT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Product ID: $PRODUCT_ID"
echo ""

# 2. List all products
echo "2. Listing all products..."
curl -s -X GET "$BASE_URL/products/" | python3 -m json.tool
echo ""

# 3. Get specific product
echo "3. Getting product by ID..."
curl -s -X GET "$BASE_URL/products/$PRODUCT_ID" | python3 -m json.tool
echo ""

# 4. Update product
echo "4. Updating product..."
curl -s -X PUT "$BASE_URL/products/$PRODUCT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 59.99,
    "stock": 60
  }' | python3 -m json.tool
echo ""

# 5. Create an order
echo "5. Creating an order..."
ORDER_RESPONSE=$(curl -s -X POST "$BASE_URL/orders/" \
  -H "Content-Type: application/json" \
  -d "{
    \"product_id\": $PRODUCT_ID,
    \"quantity\": 3
  }")
echo "$ORDER_RESPONSE" | python3 -m json.tool
ORDER_ID=$(echo "$ORDER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Order ID: $ORDER_ID"
echo ""

# 6. Get order
echo "6. Getting order by ID..."
curl -s -X GET "$BASE_URL/orders/$ORDER_ID" | python3 -m json.tool
echo ""

# 7. Update order status
echo "7. Updating order status to PAID..."
curl -s -X PUT "$BASE_URL/orders/$ORDER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "PAID"
  }' | python3 -m json.tool
echo ""

# 8. Cancel order (DELETE)
echo "8. Canceling order..."
curl -s -X DELETE "$BASE_URL/orders/$ORDER_ID" -w "\nHTTP Status: %{http_code}\n"
echo ""

# 9. Delete product
echo "9. Deleting product..."
curl -s -X DELETE "$BASE_URL/products/$PRODUCT_ID" -w "\nHTTP Status: %{http_code}\n"
echo ""

echo "All curl tests completed!"


