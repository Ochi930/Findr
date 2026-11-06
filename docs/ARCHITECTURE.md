# Architecture (M0)

**Stack:** Django 5 + Django REST Framework, PostgreSQL in production (SQLite on
a laptop), Pillow for images. Background jobs (stale-case checks, email, video
processing) arrive in M2 and M5 using Celery or Django-Q with Redis.

**Later additions, in order**

| Milestone | Addition |
|---|---|
| M1 | Server-rendered pages with a small amount of JavaScript; search with Postgres full-text and trigram matching |
| M2 | Email sending, scheduled stale-case job, station dashboard |
| M4 | Poster rendering; LLM provider adapter (swap providers via one interface) |
| M5 | pgvector for face and image embeddings, video worker |
| M7 | Separate GPU service for camera streams, isolated network, signed alerts into Findr |

**Why separate the camera service later:** it handles the most sensitive data and
needs different security, hosting and legal controls from the public website.

**Location:** plain latitude and longitude for now. PostGIS arrives with M7 when
we need distance and route queries.
