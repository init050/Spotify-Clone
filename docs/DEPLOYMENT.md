# Deployment & Environment Guide

This document provides instructions for setting up and managing the application environment using Docker Compose. The setup is optimized for a local development environment that closely mirrors a production setup.

## 1. Local Setup with Docker Compose

Our `docker-compose.yml` is configured to run the entire application stack, including the web server, database, cache, object storage, and background workers.

### Services Overview

The `docker-compose up` command will launch the following services:
-   `proxy`: Nginx reverse proxy.
-   `web`: The Django application running on Gunicorn.
-   `db`: PostgreSQL database.
-   `redis`: Redis server for caching and message brokering.
-   `minio`: S3-compatible object storage.
-   `worker`: A Celery worker for processing asynchronous tasks.
-   `beat`: The Celery beat scheduler for running periodic tasks.

### Running the Application

The **[Quick Start](../README.md#🚀-quick-start)** section in the main `README.md` provides the primary instructions for getting the application running. With the updated `docker-compose.yml`, all services, including the Celery worker and beat scheduler, will start automatically.

You no longer need to run the Celery worker in a separate terminal. The command `docker-compose up --build -d` is all you need.

## 2. Important Management Commands

Several management commands are available for administering the application. These should be run via `docker-compose exec`.

### Rebuilding the Search Index

The search functionality relies on pre-populated search vectors in the database. If you add a large amount of data to the database manually or need to reset the search index, you should run this command.

```bash
docker-compose exec web python manage.py rebuild_search_index
```
This command iterates through all searchable models (Tracks, Albums, Artists) and updates their search vectors.

### Creating a Superuser

To access the Django admin interface (`http://localhost:8000/admin/`), you will need a superuser account.

```bash
docker-compose exec web python manage.py createsuperuser
```

### Seeding Initial Data

Some commands may be available to seed the database with initial data, such as genres.

```bash
# Example for seeding genres
docker-compose exec web python manage.py seed_genres
```

## 3. Production Considerations

While this Docker Compose setup is excellent for development, a real production deployment would require additional steps:

-   **Frontend Application:** The Nginx service is configured to serve a frontend from `/frontend/build`. You would need to build your frontend application and ensure Nginx can access the static files.
-   **Managed Services:** In a cloud environment (like AWS, GCP, or Azure), you would typically replace the `db`, `redis`, and `minio` containers with managed services (e.g., RDS for PostgreSQL, ElastiCache for Redis, and S3 for object storage) for better scalability, reliability, and security.
-   **Security:**
    -   The `SECRET_KEY` must be managed securely (e.g., using a secrets manager) and not hardcoded in `.env` files.
    -   `DEBUG` must be set to `False`.
    -   SSL/TLS should be configured on the load balancer or reverse proxy.
-   **CI/CD:** A CI/CD pipeline should be set up to automate testing, building Docker images, and deploying to your production environment.
