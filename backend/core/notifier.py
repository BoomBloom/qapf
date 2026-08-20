"""Real, standalone Slack alerting for Agent 1 -- no dependency on a Claude
session being present. Posts directly to a Slack Incoming Webhook URL via a
plain HTTP request, the same way the wayfinder-scoped "monitor by exception"
plan (2026-08-20) requires: the system itself pages the operator on a real
halt or a fresh CIO memo, not a person watching a terminal.

Fails soft, on purpose: a Slack outage or a missing webhook must never be
what stops the trading pipeline from completing. Every call is best-effort
and logs a warning on failure rather than raising.
"""

import logging
import os

import requests
import tradingagents  # noqa: F401  (import side effect: loads .env via find_dotenv)

logger = logging.getLogger(__name__)

SLACK_TIMEOUT_SECONDS = 5


def send_slack_alert(text: str) -> bool:
    """Returns True if the post succeeded, False otherwise (including when
    no webhook is configured -- that's a valid, silent no-op, not an error,
    since Slack alerting is optional infrastructure, not a hard dependency)."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.debug("SLACK_WEBHOOK_URL not set -- skipping Slack alert.")
        return False

    try:
        response = requests.post(webhook_url, json={"text": text}, timeout=SLACK_TIMEOUT_SECONDS)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.warning("Slack alert failed to send (pipeline continues regardless): %s", e)
        return False
