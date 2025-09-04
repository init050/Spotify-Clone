# Technical Deep Dive

This document covers the implementation details of some of the more complex systems in the project, such as the advanced search engine and the audio processing pipeline.

## 1. Advanced Search Engine

The search functionality is powered by PostgreSQL's built-in full-text search and trigram similarity features, providing fast and relevant results.

### Database Extensions

To enable these features, the following PostgreSQL extensions must be installed. A migration (`artists/migrations/0003_enable_postgres_extensions.py`) handles this automatically.

-   `pg_trgm`: Provides functions and operators for determining the similarity of text based on trigram matching. This is used for "fuzzy" searches and suggestions.
-   `unaccent`: A text search dictionary that removes accents from characters, allowing searches to match with or without diacritics (e.g., `cafe` matches `café`).

### Search Vectors and Indexes

To avoid performing expensive full-text search queries on raw text columns, we use a dedicated `search_vector` column on searchable models (`Artist`, `Album`, `Track`, `Playlist`). This column stores a pre-processed, tsvector representation of the text content.

The following GIN (Generalized Inverted Index) indexes are in place to ensure high performance:

-   **Full-Text Search Indexes:** A `GinIndex` is applied to the `search_vector` field on each searchable model (e.g., `artist_search_vector_idx`). This allows for extremely fast lookups.
-   **Trigram Indexes:** A `GinIndex` using the `gin_trgm_ops` operator class is applied to name and title fields (e.g., `artist_name_gin_idx`). This is used for the "suggest" endpoint to find similar-sounding names.

### Management Commands

-   **`rebuild_search_index`**: This command populates the `search_vector` for all existing data. It should be run after a fresh deployment or if the logic for building the search vectors is changed.
    ```bash
    docker-compose exec web python manage.py rebuild_search_index
    ```

### Tunable Parameters

-   **Trending Algorithm:** The `compute_trending_window` task has a `lambda_decay` parameter that can be tuned to adjust how quickly the score of older items decays, making recent interactions more or less important.
-   **Suggestion Similarity:** The `SuggestView` uses a `similarity__gt=0.1` threshold. This can be increased for stricter suggestions or decreased for looser matches.

## 2. Asynchronous Audio Processing Pipeline

When a user uploads an audio file, it is not immediately available for streaming. It is processed in the background by a Celery worker to ensure the API remains responsive.

### The Process Flow

1.  **Initiate Upload:** The client sends a request to the API with the file's metadata (`filename`, `file_size`). The API returns a secure, pre-signed URL for uploading directly to the S3/Minio object store.
2.  **Direct Upload:** The client uploads the file directly to the provided URL. This offloads the bandwidth-intensive task from the web server.
3.  **Complete Upload:** The client notifies the API that the upload is complete. The API then creates a `Track` record with a `pending` status.
4.  **Enqueue Task:** The API enqueues an audio processing task in the Celery queue.
5.  **Celery Worker Processing:**
    -   A Celery worker picks up the task.
    -   It downloads the master audio file from object storage.
    -   Using **FFmpeg**, it transcodes the audio into multiple HLS variants (e.g., 64kbps, 128kbps, 256kbps), creating `.ts` segments and a `.m3u8` manifest file.
    -   It may also extract metadata or generate a waveform image.
    -   All processed files are uploaded back to the object store in a structured directory.
6.  **Finalize:** The worker updates the `Track` record's status to `published` and links to the HLS manifest file. The track is now available for streaming.
