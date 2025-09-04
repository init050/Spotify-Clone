# Spotify Clone - A Full-Featured Music Streaming Platform

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/actions)
[![Coverage](https://img.shields.io/badge/coverage-88%25-green)](./docs/TESTING.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

A comprehensive, open-source Spotify clone built with a modern Django and Docker stack. It provides a robust, scalable backend API for a feature-rich music streaming service, designed to be a standout portfolio piece for developers.

> **Note:** This project is a backend-focused application. For the full experience, you will need to connect a frontend application to this API.

<!-- Optional: Add a GIF or a key screenshot here -->
<!-- ![Project Demo GIF](./docs/assets/demo.gif) -->

## 🧭 Core Features

-   **Complete Authentication System:** Secure user registration, email verification, password reset, and session management using JWT.
-   **Two-Factor Authentication (2FA):** Enhanced security with TOTP-based 2FA.
-   **Music Catalog:** Full management of artists, albums, tracks, and genres.
-   **High-Fidelity Audio Streaming:** Securely stream audio processed into multiple quality levels using HLS.
-   **Asynchronous Audio Processing:** A background pipeline for transcoding, metadata extraction, and waveform generation.
-   **Playlists & Library:** Users can create public/private playlists, add/remove tracks, and "like" songs to build their personal library.
-   **Social Features:** Follow artists and other users, view activity feeds, and comment on albums/playlists.
-   **Advanced Search:** Powerful, fast search across tracks, albums, and artists using PostgreSQL's full-text search capabilities.
-   **Analytics & Recommendations:** Tracks listening history and provides basic trending and recommendation metrics.
-   **Containerized & Scalable:** Fully containerized with Docker and designed with a service-based architecture for scalability.

## 🛠️ Tech Stack

| Category             | Technology                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------ |
| **Backend**          | [Python](https://www.python.org/), [Django](https://www.djangoproject.com/), [Django REST Framework](https://www.django-rest-framework.org/) |
| **Database**         | [PostgreSQL](https://www.postgresql.org/)                                                              |
| **Async Tasks**      | [Celery](https://docs.celeryq.dev/), [Redis](https://redis.io/) (as Broker)                             |
| **Caching**          | [Redis](https://redis.io/)                                                                             |
| **API Documentation**| [drf-spectacular](https://drf-spectacular.readthedocs.io/) (OpenAPI/Swagger)                           |
| **Media Storage**    | [MinIO](https://min.io/) (S3-Compatible Object Storage)                                                |
- **Audio Processing** | [FFmpeg](https://ffmpeg.org/)                                                                          |
| **Containerization** | [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/)                 |
| **Testing**          | [Pytest](https://pytest.org/), [Factory Boy](https://factoryboy.readthedocs.io/), [Coverage.py](https://coverage.readthedocs.io/), [Locust](https://locust.io/) (Load Testing) |

## 🚀 Quick Start

Get a fully operational local instance of the platform running in minutes.

### Prerequisites
-   [Docker](https://docs.docker.com/get-docker/)
-   [Docker Compose](https://docs.docker.com/compose/install/)

### 1. Clone the Repository
```bash
git clone https://github.com/init050/spotify-clone.git
cd spotify-clone
```

### 2. Configure Environment Variables
Copy the example environment file. The default values are configured for the local Docker setup and should work out of the box.

```bash
cp .env.example .env
```
*You should review the file and set a new `SECRET_KEY`.*

### 3. Build and Run the Services
This command will build the Docker images and start all the services (web app, database, Redis, etc.) in the background.

```bash
docker-compose up --build -d
```

### 4. Apply Database Migrations
Once the containers are running, apply the database migrations to set up the schema.

```bash
docker-compose exec web python manage.py migrate
```

### 5. Run the Celery Worker
For asynchronous tasks like audio processing to work, you need to run at least one Celery worker. Open a **new terminal window** and run:

```bash
docker-compose exec web celery -A Spotify_Clone worker --loglevel=info
```
*(In the next step, we will update `docker-compose.yml` to run this automatically.)*

The application API is now running and available at `http://localhost:8000`.

## 🧭 Project Documentation

This `README` provides a high-level overview. For detailed information, please refer to the documents in the `/docs` directory.

| Document                               | Description                                                               |
| -------------------------------------- | ------------------------------------------------------------------------- |
| **[Project Story](./PROJECT_STORY.md)**| The "why" behind the project: problem, solution, and goals.               |
| **[Architecture](./docs/ARCHITECTURE.md)** | A high-level view of the system components and how they interact.         |
| **[API Guide](./docs/API.md)**             | How to use the API, including authentication and interactive docs.        |
| **[Deployment](./docs/DEPLOYMENT.md)**     | Guide for environment setup and running in a production-like setting.     |
| **[Technical Deep Dive](./docs/TECHNICAL_DEEP_DIVE.md)** | Details on advanced features like the search engine and async tasks.      |
| **[Testing Guide](./docs/TESTING.md)**     | Instructions on how to run the various test suites.                       |

## 🧾 License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
