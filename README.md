# Jailbreak Detection Pipeline

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the design and the list of
non-functional decisions.

## Status

Building step by step, in the order listed in ARCHITECTURE.md § 6:

- [x] Step 1 — architecture doc
- [x] Step 2 — broker + topics (`pulsar`, `topic-setup`)
- [x] Step 3 — `producer`
- [x] Step 4 — `consumer_prediction`
- [ ] Step 5 — `consumer_join`
- [ ] Step 6 — `gateway`
- [ ] Step 7 — full docker-compose wiring + end-to-end smoke test

## Step 2 — broker + topics

```bash
docker compose up -d pulsar
docker compose up topic-setup   # creates messages.raw, predictions.result, messages.dlq
```

Verify topics exist:

```bash
docker compose exec pulsar bin/pulsar-admin topics list public/default
```

Verified working:

```
persistent://public/default/messages.raw-partition-0
persistent://public/default/messages.dlq-partition-0
persistent://public/default/predictions.result-partition-0
```

## Step 3 — producer

FastAPI service exposing `POST /send` with body `{"message": "..."}`. Validates
the input, stamps `schema_version`/`id`/`produced_at`, and publishes the
result to `messages.raw`.

Unit tests run without Docker/Pulsar, using an in-memory fake publisher:

```bash
cd producer
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
```

Run against the real broker:

```bash
docker compose up -d --build producer
curl -X POST http://localhost:5000/send -H "Content-Type: application/json" -d "{\"message\": \"hello\"}"
```

Verified working: message published to `messages.raw` and consumed back with
the correct `schema_version`, `id`, `message`, and `produced_at` fields.

## Step 4 — consumer_prediction

Beam pipeline that reads `messages.raw`, classifies each message with an
ALBERT model (hot-reloaded whenever its files change on disk — same
behavior as the original prototype), and publishes to `predictions.result`
per the contract in `ARCHITECTURE.md`.

### Model weights

Not committed to git (binary, ~47MB) — copy them locally before running:

```bash
# from a checkout of the original prototype, or wherever your weights live
cp -r <path-to>/saved_models/albert_production ./models/albert_production
```

`docker-compose.yaml` bind-mounts `./models/albert_production` into the
container at `/model`.

Unit tests run without Docker/Pulsar, against the local `./models/albert_production`
checkout:

```bash
cd consumer_prediction
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
```

Run against the real broker:

```bash
docker compose up -d --build consumer_prediction
```
