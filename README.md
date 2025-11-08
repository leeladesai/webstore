# FastAPI Orders & Inventory Microservice

A production-ready microservice for managing products and orders in an online store, built with FastAPI, SQLModel, and SQLite.

## Features

- **Products CRUD**: Create, read, update, and delete products with inventory management
- **Orders CRUD**: Create orders with automatic stock reduction and status tracking
- **Payment Webhooks**: Secure webhook endpoint with HMAC-SHA256 signature verification
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Comprehensive Testing**: Tests via Swagger UI, curl, Postman, and Python scripts
- **Load Testing**: Locust configuration for performance testing
- **Deployment Ready**: Configured for deployment on Render.com

## Project Structure

```
fastapi_webstore/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database configuration
│   ├── models.py            # Data models (Product, Order)
│   └── routers/
│       ├── __init__.py
│       ├── products.py      # Product endpoints
│       ├── orders.py        # Order endpoints
│       └── webhooks.py      # Webhook endpoints
├── tests/
│   ├── __init__.py
│   ├── test_smoke.py        # Smoke tests
│   └── test_webhook.py      # Webhook tests
├── requirements.txt         # Python dependencies
├── render.yaml             # Render.com deployment config
├── locustfile.py           # Load testing configuration
├── curl_examples.sh        # Curl test examples
├── postman_collection.json # Postman collection
└── README.md               # This file
```

## Part A: Environment & Project Setup

### Python Version
- **Python 3.9+** required

### Dependencies
- **fastapi** (0.104.1): Modern web framework for building APIs
- **uvicorn** (0.24.0): ASGI server for running FastAPI
- **sqlmodel** (0.0.14): SQL database ORM with Pydantic integration
- **requests** (2.31.0): HTTP client for testing
- **locust** (2.17.0): Load testing framework
- **python-dotenv** (1.0.0): Environment variable management

## Part B: Data Modeling & Validation

### Product Model
- **Fields**: id, sku, name, price, stock
- **Constraints**:
  - `sku`: Unique, indexed
  - `price`: Must be > 0
  - `stock`: Must be >= 0
- **Indexes**: sku (unique index), name (search index)

### Order Model
- **Fields**: id, product_id, quantity, status, created_at
- **Constraints**:
  - `quantity`: Must be > 0
  - `status`: Enum (PENDING, PAID, SHIPPED, CANCELED)
  - `created_at`: Auto-generated timestamp
- **Indexes**: product_id (foreign key), status (filtering)

## Part C: Endpoints & Behavior

### Products Endpoints

#### POST /products
- **Success**: 201 Created
- **Error**: 409 Conflict (duplicate SKU)
- **Request Body**: `{sku, name, price, stock}`

#### GET /products
- **Response**: 200 OK with list of products
- **Pagination**: Optional (skip, limit parameters)

#### GET /products/{id}
- **Success**: 200 OK
- **Not Found**: 404 with `{"detail": "Product with ID {id} not found"}`

#### PUT /products/{id}
- **Update Type**: Partial updates allowed (exclude_unset=True)
- **Validation**: Rejects invalid fields via Pydantic
- **Conflict**: 409 if new SKU conflicts

#### DELETE /products/{id}
- **Success**: 204 No Content

### Orders Endpoints

#### POST /orders
- **Atomic Operation**: Reduces stock and creates order in transaction
- **Stock Check**: 409 Conflict if insufficient stock
- **Request Body**: `{product_id, quantity}`

#### GET /orders/{id}
- **Returns**: Order ID, product ID, quantity, status, created_at

#### PUT /orders/{id}
- **Updatable Fields**: status only
- **Status Transitions**: Validated (PENDING→PAID/CANCELED, PAID→SHIPPED/CANCELED)
- **Error**: 400 Bad Request for invalid transitions

#### DELETE /orders/{id}
- **Semantics**: Soft delete (changes status to CANCELED)
- **Stock Restoration**: Restores stock if order was PENDING
- **Error**: 400 if order is SHIPPED or CANCELED

## Part D: Error Handling & Contracts

### Error Cases

1. **Duplicate SKU (409 Conflict)**
   ```json
   {
     "detail": "Product with SKU 'PROD-001' already exists"
   }
   ```

2. **Insufficient Stock (409 Conflict)**
   ```json
   {
     "detail": {
       "error": "Insufficient stock",
       "requested": 10,
       "available": 5,
       "product_id": 1
     }
   }
   ```

3. **Product Not Found (404 Not Found)**
   ```json
   {
     "detail": "Product with ID 999 not found"
   }
   ```

4. **Invalid Status Transition (400 Bad Request)**
   ```json
   {
     "detail": {
       "error": "Invalid status transition",
       "current_status": "SHIPPED",
       "requested_status": "PAID",
       "message": "Cannot transition from SHIPPED to PAID"
     }
   }
   ```

5. **Invalid Webhook Signature (401 Unauthorized)**
   ```json
   {
     "detail": "Invalid webhook signature"
   }
   ```

### Concurrency Handling

- SQLite transactions handle basic concurrency
- For production: Use PostgreSQL with proper locking (SELECT FOR UPDATE)
- Document limitations: SQLite may have contention issues under high load

## Part E: API Documentation (Swagger UI)

### OpenAPI Metadata
- **Title**: Orders & Inventory Microservice
- **Version**: 1.0.0
- **Description**: Comprehensive API documentation

### Tags
- `products`: Product management operations
- `orders`: Order management operations
- `webhooks`: Webhook endpoints

### Access
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Enhanced Endpoints
- **POST /products**: Includes example request body
- **POST /orders**: Includes example request body and stock validation details

## Part F: Black-Box Testing

### Swagger UI Testing
1. Navigate to `http://localhost:8000/docs`
2. Test full flow: Create product → List → Get → Update → Delete
3. Test orders: Create → Get → Update → Cancel

### Curl Testing
Run the provided script:
```bash
chmod +x curl_examples.sh
./curl_examples.sh
```

Or set BASE_URL environment variable:
```bash
BASE_URL=https://your-render-url.onrender.com ./curl_examples.sh
```

### Postman Collection
1. Import `postman_collection.json` into Postman
2. Set `base_url` variable (local: `http://localhost:8000`, Render: your URL)
3. Set `webhook_secret` variable
4. Run collection requests

### Python Script
```bash
# Local testing
python tests/test_smoke.py

# Render testing
BASE_URL=https://your-render-url.onrender.com python tests/test_smoke.py
```

**CI Integration**: Add to `.github/workflows/test.yml` or similar CI pipeline

## Part G: Payment Webhook (Security & E2E)

### Endpoint
**POST /webhooks/payment**

### Headers
- `X-Webhook-Signature`: HMAC-SHA256 signature of request body
- `X-Event-Id`: Unique event ID (for replay protection)

### Signature Generation
```python
import hmac
import hashlib

def generate_signature(body: str, secret: str) -> str:
    return hmac.new(
        secret.encode(),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
```

### Request Body
```json
{
  "event": "payment.succeeded",
  "order_id": 123,
  "amount": 99.99,
  "currency": "USD"
}
```

### Testing
```bash
# Test with valid signature
python tests/test_webhook.py

# Test with invalid signature (should return 401)
# Test replay attack (should return 400)
```

### Security Features
- HMAC-SHA256 signature verification
- Replay attack protection via event ID tracking
- Constant-time comparison to prevent timing attacks

## Part H: Deployment on Render.com

### Deployment Approach
Using `render.yaml` for Infrastructure as Code (IaC)

### Build & Start Commands
- **Build**: `pip install -r requirements.txt`
- **Start**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **$PORT**: Provided by Render automatically

### Environment Variables
Set in Render dashboard:
- `WEBHOOK_SECRET`: Secret for webhook signature verification

### Deployment Steps
1. Push code to GitHub
2. Connect repository to Render
3. Render will detect `render.yaml` and configure service
4. Set `WEBHOOK_SECRET` in environment variables
5. Deploy

### Public URL
After deployment, access:
- API: `https://your-app.onrender.com`
- Docs: `https://your-app.onrender.com/docs`

## Part I: Post-Deployment Testing

### Re-run All Tests
1. Update `BASE_URL` to Render URL
2. Run Swagger UI tests
3. Run curl tests
4. Run Postman collection
5. Run Python scripts

### Error Testing
1. **Invalid Product ID**: GET /products/99999 → 404
2. **Insufficient Stock**: POST /orders with quantity > stock → 409

## Part J: Load Testing (Locust)

### Installation
```bash
pip install locust
```

### Run Locust
```bash
# Start Locust web UI
locust -f locustfile.py --host=http://localhost:8000

# Or use command line
locust -f locustfile.py --host=http://localhost:8000 --users 25 --spawn-rate 5 --run-time 60s
```

### Test Scenarios

#### Light Load
- Users: 25
- Spawn Rate: 5/s
- Duration: 60s

#### Heavy Load
- Users: 200
- Spawn Rate: 20/s
- Duration: 60s

### User Behavior
- **80% Reads**: GET /products
- **20% Writes**: Create products and orders

### Metrics to Record
- Median latency
- 95th percentile latency
- 99th percentile latency
- Requests per second (RPS)
- Error rate

## Part K: Reflection & Hardening

### Production Concerns

1. **Database Transactions & Migrations**
   - Migrate to PostgreSQL for production
   - Use Alembic for database migrations
   - Implement proper transaction isolation

2. **Authentication & Rate Limiting**
   - Add API key authentication for write operations
   - Implement rate limiting (e.g., using slowapi)
   - Add CORS restrictions

3. **Observability & Monitoring**
   - Structured logging (JSON format)
   - Metrics collection (Prometheus)
   - Distributed tracing (OpenTelemetry)
   - Health check endpoints

### SLA/SLO Contracts

- **Availability**: 99.9% uptime
- **Latency**: P95 < 200ms, P99 < 500ms
- **Error Rate**: < 0.1%

### Dashboards & Alerts

1. **Metrics Dashboard** (Grafana)
   - Request rate, latency, error rate
   - Database connection pool
   - Order creation rate

2. **Alerts**
   - High error rate (> 1%)
   - High latency (P95 > 500ms)
   - Database connection failures

### API Design Improvements

1. **Idempotency**: Add idempotency keys for webhook processing
2. **Pagination**: Implement cursor-based pagination for large datasets
3. **Filtering**: Add query parameters for filtering orders by status, date range
4. **Bulk Operations**: Add bulk create/update endpoints

## Quick Start

### Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Application**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Access Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

4. **Run Tests**
   ```bash
   python tests/test_smoke.py
   python tests/test_webhook.py
   ```

### Environment Variables

Create `.env` file:
```
WEBHOOK_SECRET=your-secret-key-here
BASE_URL=http://localhost:8000
```

## License

MIT License

## Author

FastAPI Webstore Assignment - Orders & Inventory Microservice

