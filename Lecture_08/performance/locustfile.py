from locust import HttpUser, between, task


class ProductUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def list_products(self):
        with self.client.get(
            "/api/v1/products?page=1&per_page=10",
            name="GET /api/v1/products",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Unexpected HTTP status: {response.status_code}"
                )
                return

            try:
                body = response.json()

                if (
                    not isinstance(body["items"], list)
                    or len(body["items"]) != 10
                    or body["total"] != 1000
                ):
                    response.failure("Unexpected product listing")
            except (ValueError, KeyError, TypeError):
                response.failure("Invalid response structure")