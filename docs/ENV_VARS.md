# Environment Variables Guide

This document provides a comprehensive list of all environment variables used to configure the application. These should be defined in a `.env` file in the project root. A `.env.example` file is provided as a template.

## Core Django Settings

| Variable     | Description                                                                                             | Default (in `.env.example`) |
| ------------ | ------------------------------------------------------------------------------------------------------- | --------------------------- |
| `SECRET_KEY` | **Required.** A secret key for a particular Django installation. This is used for cryptographic signing. | `your-secret-key`           |
| `DEBUG`      | **Required.** Toggles Django's debug mode. Should be `False` in production.                             | `True`                      |
| `ALLOWED_HOSTS` | A comma-separated list of strings representing the host/domain names that this Django site can serve. | `localhost,127.0.0.1`       |

## Database (PostgreSQL)

These variables are used by Docker Compose to initialize the PostgreSQL container and by Django to connect to it.

| Variable            | Description                            | Default (in `.env.example`) |
| ------------------- | -------------------------------------- | --------------------------- |
| `POSTGRES_DB`       | The name of the database to create.    | `spotify_clone`             |
| `POSTGRES_USER`     | The username for the database user.    | `spotify_clone`             |
| `POSTGRES_PASSWORD` | The password for the database user.    | `your-pg-password`          |
| `POSTGRES_HOST`     | The hostname of the database server.   | `db`                        |
| `POSTGRES_PORT`     | The port the database server is on.    | `5432`                      |

## Cache & Async Tasks (Redis & Celery)

Variables for connecting to the Redis server, which is used for both caching and as a message broker for Celery.

| Variable                | Description                                    | Default (in `.env.example`)       |
| ----------------------- | ---------------------------------------------- | --------------------------------- |
| `REDIS_URL`             | The connection URL for the Redis server.       | `redis://redis:6379/0`            |
| `CELERY_BROKER_URL`     | The URL for the Celery message broker.         | `redis://redis:6379/1`            |
| `CELERY_RESULT_BACKEND` | The URL for storing Celery task results.       | `redis://redis:6379/2`            |

## Media Storage (S3 / MinIO)

Configuration for the object storage service where media files (audio, images) are stored. The defaults are for the local Minio container.

| Variable                  | Description                                                                 | Default (in `.env.example`)     |
| ------------------------- | --------------------------------------------------------------------------- | ------------------------------- |
| `AWS_ACCESS_KEY_ID`       | The access key for the S3-compatible service.                               | `minioadmin`                    |
| `AWS_SECRET_ACCESS_KEY`   | The secret key for the S3-compatible service.                               | `minioadmin`                    |
| `AWS_STORAGE_BUCKET_NAME` | The name of the bucket where files will be stored.                          | `spotify-clone-media`           |
| `AWS_S3_ENDPOINT_URL`     | The full endpoint URL for the S3 service. For local Minio.                  | `http://minio:9000`             |
| `AWS_S3_CUSTOM_DOMAIN`    | The domain to use for generated URLs. For local Minio, this is `localhost`. | `localhost:9000`                |
| `AWS_LOCATION`            | The region for the bucket. Can be an empty string for Minio.                | ``                              |

## Search & Recommendations

Tunable parameters for the search and discovery features.

| Variable                     | Description                                                               | Default (in `.env.example`) |
| ---------------------------- | ------------------------------------------------------------------------- | --------------------------- |
| `SEARCH_DEFAULT_PER_PAGE`    | The default number of results per page for search results.                | `20`                        |
| `SEARCH_MAX_PER_PAGE`        | The maximum number of results per page for search results.                | `50`                        |
| `TRENDING_WINDOW_HOURS`      | The time window in hours for calculating trending content.                | `168` (7 days)              |

## Audio Processing

Settings for the audio transcoding pipeline.

| Variable                | Description                                                              | Default (in `.env.example`) |
| ----------------------- | ------------------------------------------------------------------------ | --------------------------- |
| `CATALOG_HLS_VARIANTS`  | A comma-separated list of bitrates (in kbps) to generate for HLS streams.| `64,128,256`                |
