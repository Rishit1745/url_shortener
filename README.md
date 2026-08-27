# URL Shortener & Link Analytics API

A backend service for shortening URLs and tracking click analytics, built with FastAPI, PostgreSQL, and Redis. Demonstrates core backend engineering patterns: REST API design, relational data modeling, and cache-aside caching.

🔗 **Live Demo:** https://urlshortener-production-1e5e.up.railway.app/docs

## Features

- **Shorten URLs** — generate a unique short code for any long URL
- **Redirect** — visiting a short link redirects to the original URL
- **Click Analytics** — tracks total clicks and clicks-by-day per link, with referrer logging
- **Redis Caching** — short_code → long_url lookups are cached (cache-aside pattern) to reduce database load on redirects

## Tech Stack

- **FastAPI** — REST API framework
- **PostgreSQL** (hosted on Neon) — persistent storage for links and clicks
- **SQLAlchemy** — ORM for database models and queries
- **Redis** (hosted on Upstash) — caching layer for redirect lookups
- **Railway** — deployment platform

## Architecture
Client → FastAPI → Redis (cache check) → PostgreSQL (on cache miss)
↓
Click logged → PostgreSQL


On each redirect request, the app first checks Redis for a cached `short_code → long_url` mapping. On a cache hit, it skips the database entirely. On a miss, it queries PostgreSQL, returns the result, and populates the cache with a 1-hour TTL for subsequent requests.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/shorten` | Create a short URL from a long URL |
| `GET` | `/{short_code}` | Redirect to the original URL (logs a click) |
| `GET` | `/links/{short_code}/stats` | Get total clicks and click breakdown by day |

### Example

**Request:**
```json
POST /shorten
{
  "long_url": "https://www.example.com"
}
```

**Response:**
```json
{
  "short_code": "5Ume5J",
  "long_url": "https://www.example.com"
}
```

**Stats response:**
```json
{
  "short_code": "5Ume5J",
  "long_url": "https://www.example.com",
  "total_clicks": 1,
  "clicks_by_day": [
    { "day": "2026-08-27", "count": 1 }
  ]
}
```

## Database Schema

**`links`**
| Column | Type | Description |
|--------|------|--------------|
| id | Integer | Primary key |
| short_code | String | Unique short code |
| long_url | String | Original URL |
| created_at | Timestamp | Creation time |

**`clicks`**
| Column | Type | Description |
|--------|------|--------------|
| id | Integer | Primary key |
| link_id | Integer | Foreign key → links.id |
| timestamp | Timestamp | Click time |
| referrer | String | Referring URL (nullable) |

## Running Locally

```bash
git clone https://github.com/Rishit1745/url_shortener.git
cd url_shortener
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create a `.env` file with:
DATABASE_URL=your_postgres_connection_string
REDIS_HOST=your_redis_host
REDIS_PORT=your_redis_port
REDIS_PASSWORD=your_redis_password


Run the server:
```bash
uvicorn main:app --reload
```
Visit `http://127.0.0.1:8000/docs` for the interactive API docs.

## Future Enhancements

- Rate limiting on `/shorten` to prevent abuse
- User authentication for managing personal links
- Custom short codes (vanity URLs)
- Geographic breakdown of clicks (from IP)