"""Retrieve latest update for IronOS."""

from __future__ import annotations

from dataclasses import dataclass

from aiohttp import ClientError, ClientSession

from .const import GITHUB_LATEST_RELEASES_URL
from .exceptions import UpdateException


@dataclass(kw_only=True)
class LatestRelease:
    """Latest release data."""

    tag_name: str
    name: str
    html_url: str
    body: str


class IronOSUpdate:
    """Check for IronOS updates."""

    def __init__(
        self,
        session: ClientSession,
    ) -> None:
        """Initialize IronOS release checker."""

        self._session = session
        self.url = GITHUB_LATEST_RELEASES_URL

    async def latest_release(self) -> LatestRelease:
        """Fetch latest IronOS release."""
        try:
            async with self._session.get(self.url) as response:
                data = await response.json()
                return LatestRelease(
                    tag_name=data["tag_name"],
                    name=data["name"],
                    html_url=data["html_url"],
                    body=data["body"],
                )
        except ClientError:
            raise UpdateException("Failed to fetch latest IronOS release from Github")
        except KeyError:
            raise UpdateException(
                "Failed to parse latest IronOS release from Github response"
            )
