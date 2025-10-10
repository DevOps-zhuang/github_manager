"""GitHub REST API client helpers for invitation workflows."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

import requests

DEFAULT_GITHUB_API_BASE_URL = "https://api.github.com"


class GitHubAPIError(RuntimeError):
    """Raised when the GitHub API returns an unexpected response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class TeamInfo:
    """Metadata for a GitHub team."""

    id: int
    slug: str
    name: str


class GitHubAPI:
    """Lightweight GitHub API client focused on invitation scenarios."""

    def __init__(
        self,
        *,
        token: str | None = None,
        base_url: str = DEFAULT_GITHUB_API_BASE_URL,
        session: requests.Session | None = None,
    ) -> None:
        self._token = token or os.getenv("GITHUB_TOKEN")
        if not self._token:
            raise GitHubAPIError(
                "GitHub token is required. Provide it via constructor or GITHUB_TOKEN env var."
            )

        self._base_url = base_url.rstrip("/")
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "github-manager-bot",
            }
        )

    def list_teams(self, organization: str) -> Iterator[TeamInfo]:
        """Yield all teams for a given organization."""

        url = f"{self._base_url}/orgs/{organization}/teams"
        params: dict[str, str] | None = {"per_page": "100"}
        while url:
            try:
                response = self._session.get(url, params=params, timeout=30)
            except requests.RequestException as exc:
                raise GitHubAPIError(
                    f"Network error while listing teams for organization '{organization}': {exc}"
                ) from exc
            if response.status_code >= 400:
                raise GitHubAPIError(
                    f"Failed to list teams for organization '{organization}': {response.text}",
                    status_code=response.status_code,
                )

            for payload in response.json():
                yield TeamInfo(id=payload["id"], slug=payload["slug"], name=payload["name"])

            next_link = response.links.get("next", {}).get("url")
            url = next_link
            params = None  # Subsequent requests already include params in the URL

    def get_team_by_name(self, organization: str, team_name: str) -> Optional[TeamInfo]:
        """Return team metadata by its display name (case-insensitive)."""

        normalized = team_name.strip().lower()
        for team in self.list_teams(organization):
            if team.name.lower() == normalized:
                return team
        return None

    def invite_user(self, organization: str, email: str, *, team_ids: Iterable[int] | None = None) -> requests.Response:
        """Send an invitation for a user to join an organization and optional teams."""
        payload: dict[str, object] = {"email": email}
        if team_ids:
            payload["team_ids"] = list(team_ids)

        try:
            response = self._session.post(
                f"{self._base_url}/orgs/{organization}/invitations",
                json=payload,
                timeout=30,
            )
        except requests.RequestException as exc:
            raise GitHubAPIError(
                f"Network error while inviting '{email}' to '{organization}': {exc}"
            ) from exc
        return response

    def get_rate_limit_info(self, response: requests.Response) -> dict[str, str | int | None]:
        """Extract rate limit headers from a Response for diagnostics.

        Returns a small dict with common X-RateLimit-* headers. Values are
        int when parsable, else the raw string or None.
        """
        def _parse_int(value: str | None) -> int | None:
            if value is None:
                return None
            try:
                return int(value)
            except Exception:
                return None

        headers = response.headers
        return {
            "limit": _parse_int(headers.get("X-RateLimit-Limit")),
            "remaining": _parse_int(headers.get("X-RateLimit-Remaining")),
            "reset": _parse_int(headers.get("X-RateLimit-Reset")),
            "retry-after": _parse_int(headers.get("Retry-After"))
            if headers.get("Retry-After")
            else None,
        }

    def create_team(
        self,
        organization: str,
        team_name: str,
        *,
        privacy: str = "closed",
        parent_team_slug: str | None = None,
    ) -> TeamInfo:
        """Create a team within an organization if it does not already exist."""

        payload: dict[str, str | None] = {"name": team_name, "privacy": privacy}
        if parent_team_slug:
            payload["parent_team_slug"] = parent_team_slug

        try:
            response = self._session.post(
                f"{self._base_url}/orgs/{organization}/teams",
                json=payload,
                timeout=30,
            )
        except requests.RequestException as exc:
            raise GitHubAPIError(
                f"Network error while creating team '{team_name}' in organization '{organization}': {exc}"
            ) from exc

        if response.status_code in (200, 201):
            data = response.json()
            return TeamInfo(id=data["id"], slug=data["slug"], name=data["name"])

        if response.status_code == 422:
            data = response.json()
            message = (data.get("message") or "").lower()
            if "already exists" in message:
                existing = self.get_team_by_name(organization, team_name)
                if existing:
                    return existing

            detail = data.get("message") or data.get("errors") or response.text
            raise GitHubAPIError(
                f"Failed to create team '{team_name}' in organization '{organization}': {detail}",
                status_code=response.status_code,
            )

        raise GitHubAPIError(
            f"Failed to create team '{team_name}' in organization '{organization}': {response.text}",
            status_code=response.status_code,
        )
