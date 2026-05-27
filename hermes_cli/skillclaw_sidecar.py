"""SkillClaw sidecar integration helpers."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def sidecar_config(config: dict | None) -> dict | None:
    skillclaw = config.get("skillclaw") if isinstance(config, dict) else None
    if not isinstance(skillclaw, dict) or not skillclaw.get("enabled"):
        return None
    mode = str(skillclaw.get("mode") or "").strip().lower()
    if mode != "sidecar":
        return None
    endpoint = str(skillclaw.get("endpoint") or "").strip().rstrip("/")
    if not endpoint:
        return None
    return {
        "endpoint": endpoint,
        "api_key": str(skillclaw.get("api_key") or "skillclaw"),
        "timeout": float(skillclaw.get("timeout") or 3.0),
    }


def _headers(config: dict) -> dict[str, str]:
    api_key = str(config.get("api_key") or "").strip()
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def fetch_context(
    config: dict | None,
    *,
    session_id: str,
    messages: list[dict[str, Any]],
    model: str,
    provider: str,
    api_mode: str,
) -> dict[str, Any]:
    scfg = sidecar_config(config)
    if not scfg:
        return {"context": "", "injected_skills": []}
    try:
        import httpx

        payload = {
            "session_id": session_id,
            "messages": messages,
            "model": model,
            "provider": provider,
            "api_mode": api_mode,
        }
        response = httpx.post(
            f"{scfg['endpoint']}/skillclaw/v1/context",
            json=payload,
            headers=_headers(scfg),
            timeout=scfg["timeout"],
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {"context": "", "injected_skills": []}
    except Exception as exc:
        logger.debug("SkillClaw sidecar context failed: %s", exc)
        return {"context": "", "injected_skills": []}


def record_turn(
    config: dict | None,
    *,
    session_id: str,
    messages: list[dict[str, Any]],
    response: dict[str, Any],
    injected_skills: list[str],
    model: str,
    provider: str,
    api_mode: str,
) -> None:
    scfg = sidecar_config(config)
    if not scfg:
        return
    try:
        import httpx

        payload = {
            "session_id": session_id,
            "messages": messages,
            "response": response,
            "injected_skills": injected_skills,
            "model": model,
            "provider": provider,
            "api_mode": api_mode,
        }
        response_obj = httpx.post(
            f"{scfg['endpoint']}/skillclaw/v1/record",
            json=payload,
            headers=_headers(scfg),
            timeout=scfg["timeout"],
        )
        response_obj.raise_for_status()
    except Exception as exc:
        logger.debug("SkillClaw sidecar record failed: %s", exc)


def append_context(base_prompt: Optional[str], context: str) -> Optional[str]:
    context = str(context or "").strip()
    if not context:
        return base_prompt
    base = str(base_prompt or "").strip()
    return f"{base}\n\n{context}" if base else context
