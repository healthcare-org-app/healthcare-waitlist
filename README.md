# waitlist-service

waitlist-service — domain: appointments

- **Port:** 8603
- **Language:** Python 3.11 + Flask
- **Database:** `appointments` (Postgres, table `waitlist`)
- **Event bus:** Kafka

## API

| Method    | Path                       |
|-----------|----------------------------|
| GET       | `/api/waitlist/`          |
| POST      | `/api/waitlist/`          |
| GET       | `/api/waitlist/<id>`      |
| PUT/PATCH | `/api/waitlist/<id>`      |
| DELETE    | `/api/waitlist/<id>`      |
| GET       | `/health`                  |
| GET       | `/ready`                   |

## Events

**Publishes:** (none)
**Subscribes:** appointment.cancelled

## HTTP peer dependencies

- `appointments-service`
- `patients-service`
- `notifications-service`
- `audit-log-service`

## Local dev

```bash
pip install -e ../../libs/py-healthcare-common
pip install -r requirements.txt
cp .env.example .env
(cd ../../infra && docker compose up -d postgres kafka kafka-init)
python -m app.main
```

## Tests

```bash
pytest
```
