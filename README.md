# Spotify Clone - Core Authentication Module

This project implements a robust and secure core authentication system for a Spotify clone application using Django and the Django REST Framework. It includes a wide range of features from basic registration to two-factor authentication and session management.

## Features

- **Custom User Model:** Uses email as the primary identifier.
- **JWT Authentication:** Secure stateless authentication using JSON Web Tokens with refresh token rotation and blacklisting.
- **Registration & Email Verification:** Asynchronous email verification process using Celery and Redis.
- **Password Reset:** Secure password reset flow via email.
- **Two-Factor Authentication (2FA):** Time-based One-Time Password (TOTP) implementation with backup codes for enhanced security.
- **Session Management:** Users can view and revoke their active sessions.
- **Profile & Preferences:** API endpoints for managing user profiles and application preferences.
- **Security Hardening:** Includes rate limiting on sensitive endpoints and account lockout after multiple failed login attempts.
- **Audit Logging:** Logs critical security events to a dedicated file.

## Tech Stack

- **Backend:** Django, Django REST Framework
- **Database:** PostgreSQL
- **Asynchronous Tasks:** Celery
- **Message Broker/Cache:** Redis
- **Containerization:** Docker, Docker Compose

## Setup and Installation

### Prerequisites

- Docker
- Docker Compose

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Configure Environment Variables

Create a `.env` file by copying the example file:

```bash
cp .env.example .env
```

Review the `.env` file and fill in the required values, especially the `SECRET_KEY` and any email provider settings if you are not using the console backend.

### 3. Build and Run the Services

Use Docker Compose to build the images and start the services (web app, database, and Redis).

```bash
docker-compose up --build -d
```

### 4. Apply Database Migrations

Once the containers are running, apply the database migrations:

```bash
docker-compose exec web python manage.py migrate
```

### 5. Create a Superuser (Optional)

```bash
docker-compose exec web python manage.py createsuperuser
```

The application should now be running at `http://localhost:8000`.

## API Endpoints

All endpoints are prefixed with `/api/v1/auth/`.

- `POST /register/`: Register a new user.
- `GET /verify-email/?uidb64=<uid>&token=<token>`: Verify user's email.
- `POST /login/`: Obtain JWT access and refresh tokens.
- `POST /token/refresh/`: Refresh an access token.
- `POST /logout/`: Blacklist a refresh token to log out.
- `GET/PUT /profile/`: Manage user profile.
- `GET/PUT /preferences/`: Manage user preferences.
- `POST /password-reset/request/`: Request a password reset email.
- `POST /password-reset/confirm/`: Confirm a new password.
- `GET /sessions/`: List active user sessions.
- `POST /sessions/<uuid:session_id>/revoke/`: Revoke a specific session.
- `POST /2fa/setup/`: Get a provisioning URI to set up 2FA.
- `POST /2fa/verify/`: Verify a TOTP code to enable 2FA.
- `POST /2fa/disable/`: Disable 2FA.
- `POST /2fa/login/verify/`: Complete a login when 2FA is enabled.

## Running Tests

To run the test suite and see a coverage report:

```bash
docker-compose exec web coverage run manage.py test accounts
docker-compose exec web coverage report -m
```
