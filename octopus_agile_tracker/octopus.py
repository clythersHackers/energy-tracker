from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class AgileRate:
    product_code: str
    tariff_code: str
    region_code: str
    payment_method: str
    valid_from: datetime
    valid_to: datetime
    value_exc_vat: float
    value_inc_vat: float
    fetched_at: datetime
    source_url: str


class OctopusClient:
    def __init__(self, base_url: str, api_key: str = "", timeout_seconds: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def fetch_standard_unit_rates(
        self,
        product_code: str,
        tariff_code: str,
        region_code: str,
        period_from: datetime,
        period_to: datetime,
        page_size: int,
    ) -> list[AgileRate]:
        if not product_code:
            raise ValueError("OCTOPUS_PRODUCT_CODE is required unless it can be derived from OCTOPUS_TARIFF_CODE")
        if not tariff_code:
            raise ValueError("OCTOPUS_TARIFF_CODE is required")

        path = f"/products/{quote_path(product_code)}/electricity-tariffs/{quote_path(tariff_code)}/standard-unit-rates/"
        params = {
            "period_from": iso_z(period_from),
            "period_to": iso_z(period_to),
            "page_size": str(page_size),
        }
        first_url = f"{self.base_url}{path}?{urllib.parse.urlencode(params)}"
        fetched_at = datetime.now(timezone.utc)
        rates: list[AgileRate] = []
        url = first_url

        while url:
            payload = self._get_json(url)
            for item in payload.get("results", []):
                rates.append(
                    AgileRate(
                        product_code=product_code,
                        tariff_code=tariff_code,
                        region_code=region_code,
                        payment_method=str(item.get("payment_method") or ""),
                        valid_from=parse_dt(item["valid_from"]),
                        valid_to=parse_dt(item["valid_to"]),
                        value_exc_vat=float(item["value_exc_vat"]),
                        value_inc_vat=float(item["value_inc_vat"]),
                        fetched_at=fetched_at,
                        source_url=first_url,
                    )
                )
            url = payload.get("next")

        return rates

    def _get_json(self, url: str) -> dict:
        request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "energy-tracker/0.1"})
        if self.api_key:
            token = base64.b64encode(f"{self.api_key}:".encode("utf-8")).decode("ascii")
            request.add_header("Authorization", f"Basic {token}")
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


def quote_path(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def iso_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_dt(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def dedupe_rates(rates: Iterable[AgileRate]) -> list[AgileRate]:
    seen: set[tuple[str, str, str, datetime, datetime]] = set()
    out: list[AgileRate] = []
    for rate in rates:
        key = (rate.product_code, rate.tariff_code, rate.payment_method, rate.valid_from, rate.valid_to)
        if key in seen:
            continue
        seen.add(key)
        out.append(rate)
    return out

