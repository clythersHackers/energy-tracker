from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

from .octopus import AgileRate


@dataclass(frozen=True)
class ClickHouseConfig:
    host: str
    port: int
    database: str
    table: str
    user: str
    password: str
    cluster: str
    ttl_days: int
    timeout_seconds: float


class ClickHouseClient:
    def __init__(self, cfg: ClickHouseConfig) -> None:
        self.cfg = cfg
        self.base_url = f"http://{cfg.host}:{cfg.port}/"

    def ensure_schema(self) -> None:
        local_table = f"{self.cfg.table}_local"
        on_cluster = f" ON CLUSTER `{escape_ident(self.cfg.cluster)}`" if self.cfg.cluster else ""
        ttl_clause = ttl_clause_for_days(self.cfg.ttl_days)
        schema = """
(
    product_code LowCardinality(String),
    tariff_code LowCardinality(String),
    region_code LowCardinality(String),
    payment_method LowCardinality(String),
    valid_from DateTime64(3, 'UTC'),
    valid_to DateTime64(3, 'UTC'),
    value_exc_vat Float64,
    value_inc_vat Float64,
    fetched_at DateTime64(3, 'UTC'),
    source_url String
)
""".strip()
        local_sql = (
            f"CREATE TABLE IF NOT EXISTS {ident(self.cfg.database)}.{ident(local_table)}{on_cluster} {schema} "
            "ENGINE = ReplacingMergeTree(fetched_at) "
            "PARTITION BY toYYYYMM(valid_from) "
            f"ORDER BY (product_code, tariff_code, payment_method, valid_from, valid_to){ttl_clause}"
        )
        if self.cfg.cluster:
            main_sql = (
                f"CREATE TABLE IF NOT EXISTS {ident(self.cfg.database)}.{ident(self.cfg.table)}{on_cluster} "
                f"AS {ident(self.cfg.database)}.{ident(local_table)} "
                f"ENGINE = Distributed('{escape_string(self.cfg.cluster)}', '{escape_string(self.cfg.database)}', "
                f"'{escape_string(local_table)}', rand())"
            )
        else:
            main_sql = (
                f"CREATE TABLE IF NOT EXISTS {ident(self.cfg.database)}.{ident(self.cfg.table)} "
                f"AS {ident(self.cfg.database)}.{ident(local_table)} "
                "ENGINE = ReplacingMergeTree(fetched_at) "
                "PARTITION BY toYYYYMM(valid_from) "
                f"ORDER BY (product_code, tariff_code, payment_method, valid_from, valid_to){ttl_clause}"
            )

        self.execute(local_sql)
        self.execute(main_sql)

    def insert_rates(self, rates: list[AgileRate]) -> None:
        if not rates:
            return
        rows = "\n".join(json.dumps(rate_to_row(rate), separators=(",", ":")) for rate in rates)
        sql = f"INSERT INTO {ident(self.cfg.database)}.{ident(self.cfg.table)} FORMAT JSONEachRow\n{rows}\n"
        self.execute(sql)

    def execute(self, sql: str) -> None:
        data = sql.encode("utf-8")
        request = urllib.request.Request(self.base_url, data=data, method="POST")
        request.add_header("Content-Type", "text/plain; charset=utf-8")
        if self.cfg.user or self.cfg.password:
            request.add_header("X-ClickHouse-User", self.cfg.user)
            request.add_header("X-ClickHouse-Key", self.cfg.password)
        try:
            with urllib.request.urlopen(request, timeout=self.cfg.timeout_seconds) as response:
                response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"clickhouse query failed: {exc.code} {body}") from exc


def rate_to_row(rate: AgileRate) -> dict[str, object]:
    return {
        "product_code": rate.product_code,
        "tariff_code": rate.tariff_code,
        "region_code": rate.region_code,
        "payment_method": rate.payment_method,
        "valid_from": clickhouse_dt(rate.valid_from),
        "valid_to": clickhouse_dt(rate.valid_to),
        "value_exc_vat": rate.value_exc_vat,
        "value_inc_vat": rate.value_inc_vat,
        "fetched_at": clickhouse_dt(rate.fetched_at),
        "source_url": rate.source_url,
    }


def clickhouse_dt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc)
    return value.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def ident(value: str) -> str:
    return f"`{escape_ident(value)}`"


def escape_ident(value: str) -> str:
    return value.replace("`", "``")


def escape_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def ttl_clause_for_days(days: int) -> str:
    if days <= 0:
        return ""
    return f" TTL valid_to + INTERVAL {days} DAY DELETE"
