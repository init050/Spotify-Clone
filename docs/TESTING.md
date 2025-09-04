# Testing Guide

This project includes a comprehensive suite of tests to ensure code quality, correctness, and reliability. We use a combination of unit tests, integration tests, and coverage analysis.

## Tech Stack

-   **Test Runner:** [Django's test framework](https://docs.djangoproject.com/en/stable/topics/testing/overview/) (built on Python's `unittest` module).
-   **Test Data Generation:** [Factory Boy](https://factoryboy.readthedocs.io/) for creating realistic model instances.
-   **Code Coverage:** [Coverage.py](https://coverage.readthedocs.io/) with the `django_coverage_plugin` to measure how much of the codebase is executed by tests.
-   **Load Testing:** [Locust](https://locust.io/) for simulating user traffic and measuring performance under load.

## Running Tests

All tests should be run inside the `web` container using `docker-compose exec`.

### Running All Tests

To run the entire test suite for all applications and generate a combined coverage report:

```bash
# Run tests and collect coverage data
docker-compose exec web coverage run manage.py test

# Display the coverage report in the terminal
docker-compose exec web coverage report -m
```

The `-m` flag in the coverage report shows the line numbers of missed lines, which is useful for identifying areas that need more test coverage.

### Running Tests for a Specific App

If you are working on a single application (e.g., `streaming`), you can run the tests for just that app to get faster feedback.

```bash
# Run tests for the 'streaming' app
docker-compose exec web coverage run manage.py test streaming

# Generate a coverage report scoped to that app
docker-compose exec web coverage report -m --include="streaming/*"
```

## Load Testing with Locust

A `locustfile.py` is included in the project root to simulate user behavior and load test the API.

To run a load test:
1.  Ensure the application is running (`docker-compose up -d`).
2.  Install Locust on your local machine: `pip install locust`.
3.  Start the Locust UI:
    ```bash
    locust
    ```
4.  Open your browser to `http://localhost:8089`.
5.  Specify the number of users to simulate, the spawn rate, and the host (`http://localhost:8000`), then start swarming to see real-time performance metrics.
