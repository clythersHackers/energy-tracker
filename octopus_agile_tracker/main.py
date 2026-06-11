from __future__ import annotations

import logging
import signal
import sys
import time
from datetime import datetime, timezone

from .clickhouse import ClickHouseClient, ClickHouseConfig
from .config import Config, load_config
from .octopus import OctopusClient, dedupe_rates


LOG = logging.getLogger("octopus_agile_tracker")
STOP = False


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    cfg = load_config()
    validate_config(cfg)
    clickhouse = ClickHouseClient(
        ClickHouseConfig(
            host=cfg.clickhouse_host,
            port=cfg.clickhouse_port,
            database=cfg.clickhouse_database,
            table=cfg.clickhouse_table,
            user=cfg.clickhouse_user,
            password=cfg.clickhouse_password,
            cluster=cfg.clickhouse_cluster,
            replicated=cfg.clickhouse_replicated,
            ttl_days=cfg.clickhouse_ttl_days,
            timeout_seconds=cfg.clickhouse_timeout_seconds,
        )
    )
    octopus = OctopusClient(cfg.octopus_base_url, cfg.octopus_api_key, cfg.clickhouse_timeout_seconds)

    LOG.info("ensuring clickhouse schema host=%s port=%s table=%s.%s", cfg.clickhouse_host, cfg.clickhouse_port, cfg.clickhouse_database, cfg.clickhouse_table)
    clickhouse.ensure_schema()

    while not STOP:
        poll_once(cfg, octopus, clickhouse)
        if cfg.run_once:
            return 0
        sleep_interruptibly(cfg.poll_interval.total_seconds())

    return 0


def validate_config(cfg: Config) -> None:
    if not cfg.product_code:
        raise ValueError("OCTOPUS_PRODUCT_CODE is required unless it can be derived from OCTOPUS_TARIFF_CODE")
    if not cfg.tariff_code:
        raise ValueError("OCTOPUS_TARIFF_CODE is required")
    if cfg.page_size <= 0:
        raise ValueError("OCTOPUS_PAGE_SIZE must be greater than zero")
    if not cfg.clickhouse_host:
        raise ValueError("CLICKHOUSE_HOST is required")
    if not cfg.clickhouse_database:
        raise ValueError("CLICKHOUSE_DB is required")
    if not cfg.clickhouse_table:
        raise ValueError("OCTOPUS_CLICKHOUSE_TABLE or CLICKHOUSE_TABLE is required")
    if cfg.clickhouse_ttl_days < 0:
        raise ValueError("OCTOPUS_CLICKHOUSE_TTL_DAYS must be zero or greater")


def poll_once(cfg: Config, octopus: OctopusClient, clickhouse: ClickHouseClient) -> None:
    now = datetime.now(timezone.utc)
    period_from = now - cfg.backfill
    period_to = now + cfg.lookahead
    LOG.info(
        "polling octopus product=%s tariff=%s period_from=%s period_to=%s",
        cfg.product_code,
        cfg.tariff_code,
        period_from.isoformat(),
        period_to.isoformat(),
    )
    rates = octopus.fetch_standard_unit_rates(
        product_code=cfg.product_code,
        tariff_code=cfg.tariff_code,
        region_code=cfg.region_code,
        period_from=period_from,
        period_to=period_to,
        page_size=cfg.page_size,
    )
    rates = dedupe_rates(rates)
    clickhouse.insert_rates(rates)
    LOG.info("inserted octopus rates rows=%d", len(rates))


def sleep_interruptibly(seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while not STOP:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(1.0, remaining))


def stop(_signum: int, _frame: object) -> None:
    global STOP
    STOP = True


if __name__ == "__main__":
    sys.exit(main())
