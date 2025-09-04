import os
from locust import HttpUser, task, between
from random import choice
import uuid

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class SpotifyCloneUser(HttpUser):
    wait_time = between(1, 5)
    host = os.getenv("LOCUST_HOST", "http://localhost:8000")

    def on_start(self):
        """
        Simulate user login to get JWT tokens. This is a simplified example.
        In a real test, you'd have a pool of pre-registered users.
        """
        # For simplicity, we assume a pre-existing user and a valid token.
        self.user_id = str(uuid.uuid4()) # Mock user ID
        self.track_id = str(uuid.uuid4()) # Mock track ID
        # In a real scenario, you would log in to get a token.
        # self.client.post("/api/v1/auth/login", {"email": "test@example.com", "password": "password"})
        self.headers = {}


    @task(3)
    def ingest_play_event(self):
        """
        Simulate a user playing a track.
        """
        self.client.post(
            "/api/v1/analytics/play/",
            json={
                "user_id": self.user_id,
                "track_id": self.track_id,
                "event": "progress",
                "position_ms": 15000,
                "duration_ms": 300000,
                "timestamp": "2025-08-01T12:00:30Z"
            },
            name="/api/v1/analytics/play/"
        )

    @task(1)
    def send_push_notification(self):
        """
        Simulate an internal service sending a push notification.
        This endpoint requires admin auth, which is not handled in this simple locustfile.
        We expect this to fail with a 401 or 403, but it tests the endpoint's availability.
        """
        self.client.post(
            "/api/v1/notifications/send-push/",
            json={
                "user_id": self.user_id,
                "title": "Locust Test Notification",
                "body": "This is a test notification from a load test.",
                "data": {"test_id": str(uuid.uuid4())}
            },
            name="/api/v1/notifications/send-push/"
        )

    @task(2)
    def get_content_analytics(self):
        """
        Simulate viewing analytics for a track.
        """
        self.client.get(f"/api/v1/analytics/tracks/{self.track_id}/", name="/api/v1/analytics/tracks/[track_id]")
