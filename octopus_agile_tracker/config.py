from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class Config:
    octopus_base_url: str
    octopus_api_key: str
    product_code: str
    tariff_code: str
    region_code: str
    poll_interval: timedelta
    backfill: timedelta
    lookahead: timedelta
    page_size: int
    run_once: bool
    clickhouse_host: str
    clickhouse_port: int
    clickhouse_database: str
    clickhouse_table: str
    clickhouse_user: str
    clickhouse_password: str
    clickhouse_cluster: str
    clickhouse_replicated: bool
    clickhouse_ttl_days: int
    clickhouse_timeout_seconds: float


def load_config() -> Config:
    tariff_code = env("OCTOPUS_TARIFF_CODE", "")
    product_code = env("OCTOPUS_PRODUCT_CODE", "")
    if not product_code and tariff_code:
        product_code = product_from_tariff(tariff_code)

    return Config(
        octopus_base_url=env("OCTOPUS_BASE_URL", "https://api.octopus.energy/v1"),
        octopus_api_key=env("OCTOPUS_API_KEY", ""),
        product_code=product_code,
        tariff_code=tariff_code,
        region_code=env("OCTOPUS_REGION_CODE", region_from_tariff(tariff_code)),
        poll_interval=seconds_env("OCTOPUS_POLL_SECONDS", 1800),
        backfill=seconds_env("OCTOPUS_BACKFILL_SECONDS", 86400),
        lookahead=seconds_env("OCTOPUS_LOOKAHEAD_SECONDS", 172800),
        page_size=int_env("OCTOPUS_PAGE_SIZE", 1500),
        run_once=bool_env("OCTOPUS_RUN_ONCE", False),
        clickhouse_host=env("CLICKHOUSE_HOST", "localhost"),
        clickhouse_port=int_env("CLICKHOUSE_PORT", 8123),
        clickhouse_database=env("CLICKHOUSE_DB", "default"),
        clickhouse_table=env("OCTOPUS_CLICKHOUSE_TABLE", env("CLICKHOUSE_TABLE", "octopus_agile_rates")),
        clickhouse_user=env("CLICKHOUSE_USER", env("OCTOPUS_CLICKHOUSE_USER", "")),
        clickhouse_password=env("CLICKHOUSE_PASSWORD", env("OCTOPUS_CLICKHOUSE_PASSWORD", "")),
        clickhouse_cluster=env("OCTOPUS_CLICKHOUSE_CLUSTER", env("CLICKHOUSE_CLUSTER", "")),
        clickhouse_replicated=bool_env("OCTOPUS_CLICKHOUSE_REPLICATED", bool_env("CLICKHOUSE_REPLICATED", True)),
        clickhouse_ttl_days=int_env("OCTOPUS_CLICKHOUSE_TTL_DAYS", int_env("CLICKHOUSE_TTL_DAYS", 0)),
        clickhouse_timeout_seconds=float_env("CLICKHOUSE_TIMEOUT_SECONDS", 10.0),
    )


def env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def int_env(name: str, default: int) -> int:
    raw = env(name, "")
    if raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def float_env(name: str, default: float) -> float:
    raw = env(name, "")
    if raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def seconds_env(name: str, default: int) -> timedelta:
    return timedelta(seconds=max(1, int_env(name, default)))


def bool_env(name: str, default: bool) -> bool:
    raw = env(name, "").lower()
    if raw == "":
        return default
    return raw in {"1", "true", "yes", "on"}


def product_from_tariff(tariff_code: str) -> str:
    parts = tariff_code.split("-", 2)
    if len(parts) < 3:
        return ""
    product = parts[2]
    if len(product) > 2 and product[-2] == "-":
        return product[:-2]
    return product


def region_from_tariff(tariff_code: str) -> str:
    suffix = tariff_code.rsplit("-", 1)[-1]
    if len(suffix) == 1 and suffix.isalpha():
        return suffix.upper()
    return ""
