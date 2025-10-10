"""Command-line utility for inviting normalized users into GitHub organizations."""

from __future__ import annotations

import argparse
import csv
import logging
import json
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

from invitation.constants import StandardColumns
from invitation.github_api import GitHubAPI, GitHubAPIError, TeamInfo

logger = logging.getLogger("invitation.inviter")


@dataclass(frozen=True)
class Invitee:
    email: str
    organization: str
    team: str
    parent_team: str | None = None


@dataclass
class InvitationResult:
    invitee: Invitee
    success: bool
    message: str
    timestamp: datetime


@dataclass
class InviteeEntry:
    invitee: Invitee
    row_index: int


def _invitation_key(invitee: Invitee) -> tuple[str, str, str]:
    return (
        invitee.email.lower(),
        invitee.organization.lower(),
        (invitee.team or "").lower(),
    )


def _apply_invitation_results(
    rows: List[dict[str, str]],
    entries: Sequence[InviteeEntry],
    results: Sequence[InvitationResult],
) -> None:
    status_map: defaultdict[tuple[str, str, str], List[str]] = defaultdict(list)
    for result in results:
        status = "success" if result.success else "failed"
        status_map[_invitation_key(result.invitee)].append(status)

    for entry in entries:
        key = _invitation_key(entry.invitee)
        statuses = status_map.get(key)
        if statuses:
            rows[entry.row_index]["invitation_result"] = statuses.pop(0)


def _write_back_normalized_csv(
    path: Path,
    fieldnames: Sequence[str],
    rows: Sequence[dict[str, str]],
) -> None:
    resolved_fieldnames = list(fieldnames)
    if "invitation_result" not in resolved_fieldnames:
        resolved_fieldnames.append("invitation_result")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=resolved_fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in resolved_fieldnames})


def load_invitees(
    path: Path,
    *,
    skip_successful: bool = False,
) -> tuple[List[InviteeEntry], List[str], List[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_fields = {StandardColumns.MAIL, StandardColumns.ORGANIZATION, StandardColumns.TEAM}
        missing = expected_fields.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Normalized CSV is missing required columns: {', '.join(sorted(missing))}"
            )

        fieldnames = list(reader.fieldnames or [])
        rows: List[dict[str, str]] = []
        entries: List[InviteeEntry] = []

        for raw_row in reader:
            row = {
                key: (value.strip() if isinstance(value, str) else "")
                for key, value in raw_row.items()
            }

            rows.append(row)
            row_index = len(rows) - 1

            email = row.get(StandardColumns.MAIL, "").strip()
            organization = row.get(StandardColumns.ORGANIZATION, "").strip()
            team = row.get(StandardColumns.TEAM, "").strip()
            parent_team = row.get(StandardColumns.PARENT_TEAM, "").strip() or None
            if not email or not organization:
                logger.warning("Skipping row with missing email or organization: %s", row)
                continue

            invitation_result = row.get("invitation_result", "").strip().lower()
            if skip_successful and invitation_result == "success":
                continue

            entries.append(
                InviteeEntry(
                    invitee=Invitee(
                        email=email,
                        organization=organization,
                        team=team,
                        parent_team=parent_team,
                    ),
                    row_index=row_index,
                )
            )

    return entries, fieldnames, rows


def write_results(results: Sequence[InvitationResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Mail", "Organization", "Team", "Timestamp", "Status", "Message"])
        for result in results:
            writer.writerow(
                [
                    result.invitee.email,
                    result.invitee.organization,
                    result.invitee.team,
                    result.timestamp.isoformat(),
                    "success" if result.success else "failure",
                    result.message,
                ]
            )


class InvitationProcessor:
    """Coordinates GitHub invitations for normalized data rows."""

    def __init__(
        self,
        github: GitHubAPI,
        *,
        preloaded_teams: Mapping[tuple[str, str], TeamInfo | None] | None = None,
    ) -> None:
        self._github = github
        self._team_cache: dict[tuple[str, str], TeamInfo | None] = (
            dict(preloaded_teams) if preloaded_teams else {}
        )

    def process_invitee(self, invitee: Invitee) -> InvitationResult:
        event_time = datetime.now(timezone.utc)
        team_info = None
        if invitee.team:
            team_info = self._ensure_team(invitee.organization, invitee.team, invitee.parent_team)
            if team_info is None:
                return InvitationResult(
                    invitee=invitee,
                    success=False,
                    message="Team not found for organization",
                    timestamp=event_time,
                )

        # Try inviting with simple retry/backoff for rate-limit responses
        max_attempts = 3
        attempt = 0
        last_response = None
        last_exc: Exception | None = None
        while attempt < max_attempts:
            attempt += 1
            try:
                response = self._github.invite_user(
                    invitee.organization,
                    invitee.email,
                    team_ids=[team_info.id] if team_info else None,
                )
                last_response = response
            except GitHubAPIError as exc:
                last_exc = exc
                # Network errors are worth retrying with backoff
                if attempt < max_attempts:
                    wait = 2 ** attempt
                    logger.warning(
                        "Network error inviting %s (attempt %s/%s): %s — retrying in %ss",
                        invitee.email,
                        attempt,
                        max_attempts,
                        exc,
                        wait,
                    )
                    import time

                    time.sleep(wait)
                    continue
                else:
                    return InvitationResult(
                        invitee=invitee,
                        success=False,
                        message=str(exc),
                        timestamp=event_time,
                    )

            # If we have a response, check for rate-limit and possibly retry
            if last_response is not None:
                if last_response.status_code in (429, 403):
                    rate_info = self._github.get_rate_limit_info(last_response)
                    remaining = rate_info.get("remaining")
                    retry_after = rate_info.get("retry-after")
                    if remaining == 0 or last_response.status_code == 429:
                        # Wait and retry. Ensure wait is numeric.
                        wait_val = retry_after if isinstance(retry_after, int) else None
                        wait = float(wait_val or (2 ** attempt))
                        logger.warning(
                            "Rate limited when inviting %s (attempt %s/%s). Waiting %ss. rate=%s",
                            invitee.email,
                            attempt,
                            max_attempts,
                            wait,
                            rate_info,
                        )
                        if attempt < max_attempts:
                            import time

                            time.sleep(wait)
                            continue
                        # fall through to produce failure message with rate info
                # otherwise break loop to process response
                break

        # After retry loop, prefer last_response if available
        response = last_response
        if response is None and last_exc is not None:
            return InvitationResult(
                invitee=invitee,
                success=False,
                message=str(last_exc),
                timestamp=event_time,
            )

        if response is None:
            return InvitationResult(
                invitee=invitee,
                success=False,
                message="No response from GitHub API",
                timestamp=event_time,
            )

        if response.status_code in (201, 202):
            message = "Invitation created"
            return InvitationResult(
                invitee=invitee,
                success=True,
                message=message,
                timestamp=event_time,
            )

        if response.status_code == 204:
            return InvitationResult(
                invitee=invitee,
                success=True,
                message="User is already a member of the organization",
                timestamp=event_time,
            )

        if response.status_code == 422:
            # Include full response body to help diagnose Validation Failed
            try:
                payload = response.json()
            except Exception:
                payload = None

            # Prefer structured message when available, else fall back to raw text
            detail = None
            if isinstance(payload, dict):
                # Compose a compact detail string from message/errors if present
                msg = payload.get("message")
                errs = payload.get("errors")
                if msg and errs:
                    detail = f"{msg}; errors={errs}"
                elif msg:
                    detail = msg
                elif errs:
                    detail = json.dumps(errs, ensure_ascii=False)

            if not detail:
                detail = getattr(response, "text", "")

            # Truncate overly long details for CSV cells while keeping full JSON in logs
            truncated = detail if len(detail) <= 200 else detail[:197] + "..."
            logger.debug("Invite 422 response for %s@%s: %s", invitee.email, invitee.organization, detail)

            return InvitationResult(
                invitee=invitee,
                success=False,
                message=f"Unprocessable invitation: {truncated}",
                timestamp=event_time,
            )

        if response.status_code == 409:
            return InvitationResult(
                invitee=invitee,
                success=False,
                message="Conflict inviting user (possibly pending invite)",
                timestamp=event_time,
            )

        return InvitationResult(
            invitee=invitee,
            success=False,
            message=f"Unexpected status {response.status_code}: {getattr(response, 'text', '')}",
            timestamp=event_time,
        )

    def process_group(self, invitees: Iterable[Invitee]) -> List[InvitationResult]:
        return [self.process_invitee(invitee) for invitee in invitees]

    def _ensure_team(
        self,
        organization: str,
        team_name: str,
        parent_team_name: str | None,
    ) -> TeamInfo | None:
        cache_key = (organization.lower(), team_name.lower())
        if cache_key not in self._team_cache:
            try:
                team = self._github.get_team_by_name(organization, team_name)
            except GitHubAPIError as exc:
                logger.error("Failed to resolve team '%s' in org '%s': %s", team_name, organization, exc)
                team = None
            if team is None and parent_team_name:
                parent = self._github.get_team_by_name(organization, parent_team_name)
                if parent is None:
                    try:
                        parent = self._github.create_team(organization, parent_team_name)
                    except GitHubAPIError as exc:
                        logger.error(
                            "Failed to create parent team '%s' in org '%s': %s",
                            parent_team_name,
                            organization,
                            exc,
                        )
                        parent = None
                parent_slug = parent.slug if parent else None
                try:
                    team = self._github.create_team(
                        organization,
                        team_name,
                        parent_team_slug=parent_slug,
                    )
                except GitHubAPIError as exc:
                    logger.error(
                        "Failed to create team '%s' under parent '%s' in org '%s': %s",
                        team_name,
                        parent_team_name,
                        organization,
                        exc,
                    )
                else:
                    self._team_cache[cache_key] = team
                    return team

            if team is None:
                try:
                    team = self._github.create_team(organization, team_name)
                except GitHubAPIError as exc:
                    logger.error(
                        "Failed to create team '%s' in organization '%s': %s",
                        team_name,
                        organization,
                        exc,
                    )
            self._team_cache[cache_key] = team
        return self._team_cache[cache_key]


def _group_invitees(invitees: Sequence[Invitee]) -> Mapping[tuple[str, str, str | None], List[Invitee]]:
    groups: dict[tuple[str, str, str | None], List[Invitee]] = defaultdict(list)
    for invitee in invitees:
        key = (invitee.organization, invitee.team, invitee.parent_team)
        groups[key].append(invitee)
    return groups


def _collect_teams_by_org(invitees: Sequence[Invitee]) -> Mapping[str, set[tuple[str, str | None]]]:
    teams_by_org: dict[str, set[tuple[str, str | None]]] = defaultdict(set)
    for invitee in invitees:
        if invitee.team:
            teams_by_org[invitee.organization].add((invitee.team, invitee.parent_team))
    return teams_by_org


def _ensure_teams_exist(
    github: GitHubAPI,
    teams_by_org: Mapping[str, set[tuple[str, str | None]]],
) -> dict[tuple[str, str], TeamInfo | None]:
    """Ensure teams exist once per organization and return a cache for lookups."""

    cache: dict[tuple[str, str], TeamInfo | None] = {}
    for organization, team_defs in teams_by_org.items():
        if not team_defs:
            continue

        try:
            existing = {
                team.name.lower(): team
                for team in github.list_teams(organization)
            }
        except GitHubAPIError as exc:
            logger.error(
                "Failed to list teams for organization '%s': %s", organization, exc
            )
            existing = {}

        for team_name, parent_team in sorted(team_defs):
            normalized_key = team_name.lower()
            cache_key = (organization.lower(), normalized_key)
            team_info = existing.get(normalized_key)
            if team_info:
                cache[cache_key] = team_info
                continue

            try:
                parent_slug = None
                if parent_team:
                    parent_info = github.get_team_by_name(organization, parent_team)
                    if parent_info is None:
                        try:
                            parent_info = github.create_team(organization, parent_team)
                        except GitHubAPIError as exc:
                            logger.error(
                                "Failed to create parent team '%s' in organization '%s': %s",
                                parent_team,
                                organization,
                                exc,
                            )
                            parent_info = None
                        else:
                            existing[parent_team.lower()] = parent_info
                    parent_slug = parent_info.slug if parent_info else None
                team_info = github.create_team(
                    organization,
                    team_name,
                    parent_team_slug=parent_slug,
                )
            except GitHubAPIError as exc:
                logger.error(
                    "Failed to create team '%s' in organization '%s': %s",
                    team_name,
                    organization,
                    exc,
                )
                cache[cache_key] = None
            else:
                logger.info(
                    "Created team '%s' in organization '%s'",
                    team_name,
                    organization,
                )
                cache[cache_key] = team_info
                existing[normalized_key] = team_info

    return cache


def _filter_invitees(
    entries: Sequence[InviteeEntry],
    *,
    organizations: Sequence[str] | None = None,
    teams: Sequence[str] | None = None,
) -> List[InviteeEntry]:
    if not organizations and not teams:
        return list(entries)

    org_set = {value.lower() for value in organizations} if organizations else None
    team_set = {value.lower() for value in teams} if teams else None

    filtered: List[InviteeEntry] = []
    for entry in entries:
        invitee = entry.invitee
        org_match = True if org_set is None else invitee.organization.lower() in org_set
        team_match = True
        if team_set is not None:
            if invitee.team:
                team_match = invitee.team.lower() in team_set
            else:
                team_match = "" in team_set

        if org_match and team_match:
            filtered.append(entry)

    return filtered


def run_invitation_workflow(
    invitees: Sequence[Invitee],
    github: GitHubAPI,
    *,
    mode: str,
    per_invite_delay: float = 0.5,
) -> List[InvitationResult]:
    teams_by_org = _collect_teams_by_org(invitees)
    if teams_by_org:
        total_teams = sum(len(team_names) for team_names in teams_by_org.values())
        logger.info(
            "Preparing %s teams across %s organizations before sending invitations",
            total_teams,
            len(teams_by_org),
        )
    preloaded_teams = _ensure_teams_exist(github, teams_by_org)

    processor = InvitationProcessor(github, preloaded_teams=preloaded_teams)
    results: List[InvitationResult] = []

    if mode == "individual":
        for invitee in invitees:
            result = processor.process_invitee(invitee)
            results.append(result)
            if per_invite_delay and per_invite_delay > 0:
                import time

                time.sleep(per_invite_delay)
    elif mode == "grouped":
        groups = _group_invitees(invitees)
        for (organization, team, parent_team), group_invitees in groups.items():
            logger.info(
                "Inviting %s users for organization='%s' team='%s'",
                len(group_invitees),
                organization,
                team or "<org-only>",
            )
            results.extend(processor.process_group(group_invitees))
            if per_invite_delay and per_invite_delay > 0:
                import time

                time.sleep(per_invite_delay)
    else:
        raise ValueError(f"Unsupported invitation mode: {mode}")

    return results


def _infer_enterprise_key(input_path: Path) -> str | None:
    """Infer enterprise key from path (customize/<Enterprise>/... -> <enterprise>)."""

    for parent in input_path.parents:
        if parent.name.lower() == "customize" and parent != input_path:
            try:
                enterprise_dir = input_path.relative_to(parent).parts[0]
            except ValueError:
                continue
            return enterprise_dir.lower()

    filename = input_path.stem
    if filename.startswith("normalized_"):
        remainder = filename.removeprefix("normalized_")
        return remainder.split("_")[0].lower()

    return None


def _default_report_path(enterprise_key: str | None) -> Path:
    suffix = f"{enterprise_key}_invitation_results.csv" if enterprise_key else "invitation_results.csv"
    return Path("invitation") / "reports" / suffix


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Invite normalized users into GitHub organizations.")
    parser.add_argument("input", type=Path, help="Path to normalized CSV file (Mail,Organization,Team).")
    parser.add_argument(
        "--mode",
        choices=("individual", "grouped"),
        default="grouped",
        help="Invitation mode: individual per row, or grouped by organization/team.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Where to write the invitation result CSV (default based on enterprise key).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, do not call the GitHub API; simply print the planned invitations.",
    )
    parser.add_argument(
        "--per-invite-delay",
        type=float,
        default=0.5,
        help="Seconds to wait after each invite to avoid rate-limit bursts (default 0.5).",
    )
    parser.add_argument(
        "--organization",
        action="append",
        dest="organizations",
        help="Limit invitations to specific organization names (match normalized CSV Organization column).",
    )
    parser.add_argument(
        "--team",
        action="append",
        dest="teams",
        help="Limit invitations to specific team names (match normalized CSV Team column).",
    )
    parser.add_argument(
        "--parent-team",
        type=str,
        default=None,
        help="Optional parent team name to use when creating teams (applies to all invitees).",
    )
    parser.add_argument(
        "--team-prefix",
        type=str,
        default=None,
        help="Optional prefix to prepend to every team name before lookup/creation.",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Override GitHub token (defaults to GITHUB_TOKEN environment variable).",
    )
    parser.add_argument(
        "--enterprise",
        type=str,
        default=None,
        help="Enterprise key for reporting (default inferred from input path).",
    )
    parser.add_argument(
        "--skip-successful",
        action="store_true",
        help="Skip rows already marked with invitation_result=success in the normalized CSV.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = _build_parser()
    args = parser.parse_args(argv)

    enterprise_key = (args.enterprise or "").strip().lower() or _infer_enterprise_key(args.input)

    entries, fieldnames, rows = load_invitees(args.input, skip_successful=args.skip_successful)
    if not entries:
        logger.warning("No invitees found in %s", args.input)
        return

    selected_entries = _filter_invitees(
        entries,
        organizations=args.organizations,
        teams=args.teams,
    )
    if not selected_entries:
        logger.warning("No invitees match the provided filters.")
        return

    report_path = args.report or _default_report_path(enterprise_key)
    default_parent_team = (args.parent_team or "").strip() or None
    team_prefix = (args.team_prefix or "").strip()

    if team_prefix:
        for entry in selected_entries:
            team_value = entry.invitee.team
            if not team_value:
                continue
            if team_value.startswith(team_prefix):
                prefixed_team = team_value
            else:
                prefixed_team = f"{team_prefix}{team_value}"
            if prefixed_team != team_value:
                entry.invitee = replace(entry.invitee, team=prefixed_team)
            rows[entry.row_index][StandardColumns.TEAM] = prefixed_team

    invitee_payload: List[Invitee] = []
    for entry in selected_entries:
        invitee = entry.invitee
        if default_parent_team is not None and invitee.parent_team != default_parent_team:
            invitee = replace(invitee, parent_team=default_parent_team)
        if invitee is not entry.invitee:
            entry.invitee = invitee
        invitee_payload.append(invitee)

    if args.dry_run:
        for invitee in invitee_payload:
            logger.info(
                "DRY RUN: would invite email=%s organization=%s team=%s parent=%s",
                invitee.email,
                invitee.organization,
                invitee.team or "<org-only>",
                invitee.parent_team or "<none>",
            )
        return

    try:
        github = GitHubAPI(token=args.token)
    except GitHubAPIError as exc:
        logger.error("Failed to initialize GitHub API: %s", exc)
        raise SystemExit(1) from exc

    results = run_invitation_workflow(invitee_payload, github, mode=args.mode, per_invite_delay=args.per_invite_delay)
    write_results(results, report_path)

    _apply_invitation_results(rows, selected_entries, results)
    _write_back_normalized_csv(args.input, fieldnames, rows)

    for result in results:
        log_fn = logger.info if result.success else logger.error
        log_fn(
            "INVITATION %s timestamp=%s email=%s organization=%s team=%s message=%s",
            "SUCCESS" if result.success else "FAILURE",
            result.timestamp.isoformat(),
            result.invitee.email,
            result.invitee.organization,
            result.invitee.team or "<org-only>",
            result.message,
        )

    successes = sum(1 for result in results if result.success)
    failures = len(results) - successes
    logger.info("Invitations complete: %s succeeded, %s failed", successes, failures)


if __name__ == "__main__":  # pragma: no cover
    main()
