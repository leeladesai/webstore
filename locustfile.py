"""
Locust load testing script
Part J: Load Testing (Locust) Exploration
"""
from locust import HttpUser, task, between
import random
import string


def random_sku():
    """Generate a random SKU for testing"""
    return f"LOAD-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"


class StoreUser(HttpUser):
    """
    Simulates user behavior:
    - 80% reads (GET /products)
    - 20% writes (create products and orders)
    """
    wait_time = between(0.1, 0.5)  # Wait between 100-500ms between tasks
    
    def on_start(self):
        """Called when a simulated user starts"""
        # Create a product for this user to use in orders
        self.product_id = None
        self.created_products = []
    
    @task(8)
    def list_products(self):
        """GET /products - 80% of requests (read-heavy)"""
        self.client.get("/products/")
    
    @task(2)
    def create_product(self):
        """POST /products - Create a product"""
        sku = random_sku()
        product_data = {
            "sku": sku,
            "name": f"Load Test Product {sku}",
            "price": round(random.uniform(10.0, 1000.0), 2),
            "stock": random.randint(10, 100)
        }
        response = self.client.post("/products/", json=product_data)
        if response.status_code == 201:
            self.product_id = response.json()["id"]
            self.created_products.append(self.product_id)
    
    @task(1)
    def create_order(self):
        """POST /orders - Create an order (if we have a product)"""
        if self.product_id:
            order_data = {
                "product_id": self.product_id,
                "quantity": random.randint(1, 5)
            }
            self.client.post("/orders/", json=order_data)
    
    @task(1)
    def get_order(self):
        """GET /orders/{id} - Get a specific order"""
        # Try to get a random order (will 404 sometimes, that's ok)
        order_id = random.randint(1, 100)
        self.client.get(f"/orders/{order_id}")
    
    @task(1)
    def get_product(self):
        """GET /products/{id} - Get a specific product"""
        if self.created_products:
            product_id = random.choice(self.created_products)
            self.client.get(f"/products/{product_id}")
        else:
            # Try a random ID
            product_id = random.randint(1, 100)
            self.client.get(f"/products/{product_id}")


