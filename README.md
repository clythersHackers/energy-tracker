# Energy Tracker

Containerised Octopus Agile tariff poller for a Nomad cluster. It polls
Octopus Energy half-hourly electricity tariff rates and stores them in
ClickHouse for later analysis against weather, consumption, and prediction
datasets.

The service uses only Python standard-library modules. Octopus is read via the
public REST API, and ClickHouse is written through the HTTP interface.

## Configuration

Required:

- `OCTOPUS_TARIFF_CODE`, for example your active Octopus Agile import tariff code.

Usually set explicitly:

- `OCTOPUS_PRODUCT_CODE`; if omitted, it is derived from the tariff code.
- `OCTOPUS_REGION_CODE`; if omitted, it is derived from the tariff suffix.
- `CLICKHOUSE_HOST`, default `localhost`.
- `CLICKHOUSE_PORT`, default `8123`.

Optional:

- `OCTOPUS_API_KEY`; not normally required for product/tariff endpoints.
- `OCTOPUS_POLL_SECONDS`, default `1800`.
- `OCTOPUS_BACKFILL_SECONDS`, default `86400`.
- `OCTOPUS_LOOKAHEAD_SECONDS`, default `172800`.
- `OCTOPUS_PAGE_SIZE`, default `1500`.
- `OCTOPUS_RUN_ONCE`, default `false`.
- `CLICKHOUSE_DB`, default `default`.
- `OCTOPUS_CLICKHOUSE_TABLE` or `CLICKHOUSE_TABLE`, default `octopus_agile_rates`.
- `CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD`, optional.
- `OCTOPUS_CLICKHOUSE_CLUSTER` or `CLICKHOUSE_CLUSTER`, optional.
- `OCTOPUS_CLICKHOUSE_TTL_DAYS` or `CLICKHOUSE_TTL_DAYS`, default `0` (disabled).
- `CLICKHOUSE_TIMEOUT_SECONDS`, default `10`.

## ClickHouse Schema

The table is created automatically. When `OCTOPUS_CLICKHOUSE_CLUSTER` is set,
the service creates:

- `default.octopus_agile_rates_local` on the ClickHouse cluster
- `default.octopus_agile_rates` as a Distributed table

When `OCTOPUS_CLICKHOUSE_TTL_DAYS` is set, stored tariff rows are eligible for
deletion after their `valid_to` timestamp plus the configured number of days.

In a non-clustered local setup it creates:

- `default.octopus_agile_rates_local`
- `default.octopus_agile_rates`

The main table uses `ReplacingMergeTree(fetched_at)` and is ordered by product,
tariff, payment method, and interval. Repeated polls can therefore insert the
same tariff intervals without creating a permanent logical duplicate after
ClickHouse merges.

## Local Run

```sh
OCTOPUS_TARIFF_CODE=<your-tariff-code> \
CLICKHOUSE_HOST=127.0.0.1 \
python -m octopus_agile_tracker.main
```

## Container

```sh
docker build -t energy-tracker:dev .
docker run --rm \
  -e OCTOPUS_TARIFF_CODE=<your-tariff-code> \
  -e CLICKHOUSE_HOST=<clickhouse-host> \
  -e CLICKHOUSE_PORT=8123 \
  energy-tracker:dev
```

Version tags in the form `energy-tracker-<version>` are built by GitHub Actions
and pushed to:

```text
ghcr.io/clythershackers/energy-tracker
```
