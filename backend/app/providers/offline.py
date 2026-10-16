from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

from app.domain.run_snapshot import RunSnapshot
from app.providers.protocols import ProviderResponse
from app.schemas import SourceSnapshot


class UnavailableSourceProvider:
    def __init__(self, warning: str | None = None) -> None:
        self.warning = warning or "Research providers are not configured; no external evidence was collected."

    async def collect(self, _run: RunSnapshot, _stage: str) -> ProviderResponse[list[SourceSnapshot]]:
        return ProviderResponse(
            status="unavailable",
            provider="unconfigured",
            value=[],
            warning=self.warning,
        )


class StaticFixtureSourceProvider:
    """Explicitly local demo source provider. It never represents live evidence."""

    def __init__(self, sources: list[SourceSnapshot] | None = None) -> None:
        self.sources = sources or []

    async def collect(self, _run: RunSnapshot, _stage: str) -> ProviderResponse[list[SourceSnapshot]]:
        return ProviderResponse(status="available", provider="offline_fixture", value=list(self.sources))


def fixture_source(title: str, text: str, publisher: str = "Offline demonstration") -> SourceSnapshot:
    retrieved = datetime.now(timezone.utc)
    identity = sha256(f"{title}\0{publisher}\0{text}".encode()).hexdigest()[:10]
    return SourceSnapshot(
        id=f"source-{identity}",
        title=title,
        url="offline://fixture/" + identity,
        publisher=publisher,
        retrieval_date=retrieved,
        content_hash=sha256(text.encode()).hexdigest(),
        stored_text=text,
        origin="offline_fixture",
        provider="offline_fixture",
    )
