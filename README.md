# Energy Tracker

Containerised Octopus Agile tariff poller for the home Nomad cluster. It polls
Octopus Energy half-hourly electricity tariff rates and stores them in
ClickHouse for later analysis against weather, consumption, and prediction
datasets.

The service uses only Python standard-library modules. Octopus is read via the
public REST API, and ClickHouse is written through the HTTP interface.

## Configuration

Required:

- `OCTOPUS_TARIFF_CODE`, for example `E-1R-AGILE-FLEX-22-11-25-A`.

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

The table is created automatically. In the Nomad job, `OCTOPUS_CLICKHOUSE_CLUSTER`
is set to `muthra_cluster`, so the service creates:

- `default.octopus_agile_rates_local` on the ClickHouse cluster
- `default.octopus_agile_rates` as a Distributed table

The Nomad job sets `OCTOPUS_CLICKHOUSE_TTL_DAYS=730`, so stored tariff rows are
eligible for deletion two years after their `valid_to` timestamp.

In a non-clustered local setup it creates:

- `default.octopus_agile_rates_local`
- `default.octopus_agile_rates`

The main table uses `ReplacingMergeTree(fetched_at)` and is ordered by product,
tariff, payment method, and interval. Repeated polls can therefore insert the
same tariff intervals without creating a permanent logical duplicate after
ClickHouse merges.

## Local Run

```sh
OCTOPUS_TARIFF_CODE=E-1R-AGILE-FLEX-22-11-25-A \
CLICKHOUSE_HOST=127.0.0.1 \
python -m octopus_agile_tracker.main
```

## Container

```sh
docker build -t energy-tracker:dev .
docker run --rm \
  -e OCTOPUS_TARIFF_CODE=E-1R-AGILE-FLEX-22-11-25-A \
  -e CLICKHOUSE_HOST=host.containers.internal \
  -e CLICKHOUSE_PORT=8123 \
  energy-tracker:dev
```

Version tags in the form `energy-tracker-<version>` are built by GitHub Actions
and pushed to:

```text
ghcr.io/clythershackers/energy-tracker
```
