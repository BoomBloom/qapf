from pydantic import BaseModel, Field


class FeedHealth(BaseModel):
    feed: str
    source: str
    status: str = Field(description="'ok' | 'stale' | 'gap' | 'drift' | 'down'")
    latest_observation: str | None = None
    days_since_latest: int | None = None
    n_observations: int | None = None
    expected_cadence: str | None = None
    gaps_detected: list[str] = []
    detail: str = ""


class DataHealthReport(BaseModel):
    as_of: str
    feeds_checked: int
    ok: int
    degraded: int
    down: int
    feeds: list[FeedHealth]
    verdict: str
