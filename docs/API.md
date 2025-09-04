# API Guide: Interactive Documentation

This project uses the [OpenAPI standard](https://www.openapis.org/) and `drf-spectacular` to provide live, interactive API documentation. This is the best way to explore and test the API endpoints.

## 1. Accessing the Interactive Docs

Once the project is running locally, you can access the API documentation through your browser at the following URLs:

-   **Swagger UI:** [`http://localhost:8000/api/schema/swagger-ui/`](http://localhost:8000/api/schema/swagger-ui/)
    -   A rich, interactive UI that allows you to make API calls directly from the browser.
-   **ReDoc:** [`http://localhost:8000/api/schema/redoc/`](http://localhost:8000/api/schema/redoc/)
    -   A clean, hierarchical documentation view, great for reading and understanding the API structure.

The raw OpenAPI schema file is also available at `http://localhost:8000/api/schema/`.

## 2. Authenticating with the API

Most API endpoints require authentication. To use the interactive docs for protected endpoints, you first need to get a JWT (JSON Web Token) and then authorize your session in the Swagger UI.

### Step A: Get Your Access Token

1.  First, you need a user account. You can create one via the API (`/api/v1/accounts/register/`) or by creating a superuser (`docker-compose exec web python manage.py createsuperuser`).
2.  Use the `login` endpoint to get your access and refresh tokens.

**Example using cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "your-password"}'
```

The response will look like this:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
Copy the `access` token value.

### Step B: Authorize in Swagger UI

1.  Navigate to the [Swagger UI](http://localhost:8000/api/schema/swagger-ui/).
2.  Click the green **"Authorize"** button near the top right of the page.
3.  In the popup window, paste your access token into the `HttpBearer` value field in the format `Bearer <your_access_token>`.
    -   **Important:** You must include the word `Bearer` followed by a space before the token.
    -   Example: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
4.  Click **"Authorize"** and then **"Close"**.

You are now authenticated! All subsequent requests you make through the Swagger UI will include the necessary `Authorization` header, allowing you to test all protected endpoints.
