import os
from datetime import datetime, timezone

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dynatrace")

ENV_URL = os.environ.get("DYNATRACE_ENV_URL", "").rstrip("/")
API_TOKEN = os.environ.get("DYNATRACE_API_TOKEN", "")
TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL", "")

_HEADERS = {"Authorization": f"Api-Token {API_TOKEN}"}


def _api_get(path: str, params: dict | None = None) -> dict:
    resp = httpx.get(f"{ENV_URL}{path}", params=params, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _api_post(path: str, json: dict | None = None) -> dict:
    resp = httpx.post(f"{ENV_URL}{path}", json=json, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json() if resp.content else {"status": "ok"}


@mcp.tool()
def list_problems(
    status: str = "OPEN",
    from_time: str = "now-2h",
    to_time: str = "now",
) -> str:
    """Lista problemas detectados pelo Dynatrace.

    Args:
        status: OPEN ou CLOSED
        from_time: Início do período (ex: 'now-2h', 'now-1d', ISO 8601)
        to_time: Fim do período (ex: 'now', ISO 8601)
    """
    data = _api_get(
        "/api/v2/problems",
        params={
            "problemSelector": f'status("{status}")',
            "from": from_time,
            "to": to_time,
        },
    )

    problems = data.get("problems", [])
    if not problems:
        return f"Nenhum problema {status} no período {from_time} → {to_time}."

    lines = [f"**{len(problems)} problema(s) {status}:**\n"]
    for p in problems:
        severity = p.get("severityLevel", "?")
        title = p.get("title", "?")
        pid = p.get("problemId", "?")
        impact = p.get("impactLevel", "?")
        start = p.get("startTime", "?")
        lines.append(
            f"- **[{severity}]** {title}\n"
            f"  ID: `{pid}` | Impacto: {impact} | Início: {start}"
        )

    total = data.get("totalCount", len(problems))
    if total > len(problems):
        lines.append(f"\n_(mostrando {len(problems)} de {total} problemas)_")

    return "\n".join(lines)


@mcp.tool()
def get_problem(problem_id: str) -> str:
    """Detalhes de um problema específico.

    Args:
        problem_id: ID do problema (ex: 'P-12345678')
    """
    d = _api_get(f"/api/v2/problems/{problem_id}")

    lines = [
        f"# {d.get('title', '?')}",
        f"- **Status:** {d.get('status', '?')}",
        f"- **Severidade:** {d.get('severityLevel', '?')}",
        f"- **Impacto:** {d.get('impactLevel', '?')}",
        f"- **Início:** {d.get('startTime', '?')}",
        f"- **Fim:** {d.get('endTime', 'em andamento')}",
    ]

    rc = d.get("rootCauseEntity")
    if rc:
        eid = rc.get("entityId", {})
        lines.append(
            f"- **Root cause:** {rc.get('name', '?')} ({eid.get('type', '?')})"
        )

    affected = d.get("affectedEntities", [])
    if affected:
        lines.append(f"\n**Entidades afetadas ({len(affected)}):**")
        for e in affected[:15]:
            eid = e.get("entityId", {})
            lines.append(f"  - {e.get('name', '?')} (`{eid.get('type', '?')}`)")

    evidence = d.get("evidenceDetails", {}).get("details", [])
    if evidence:
        lines.append(f"\n**Evidências ({len(evidence)}):**")
        for ev in evidence[:10]:
            lines.append(
                f"  - [{ev.get('evidenceType', '?')}] {ev.get('displayName', '?')}"
            )

    mgmt_zones = d.get("managementZones", [])
    if mgmt_zones:
        names = ", ".join(z.get("name", "?") for z in mgmt_zones)
        lines.append(f"\n**Management zones:** {names}")

    return "\n".join(lines)


@mcp.tool()
def get_problem_comments(problem_id: str) -> str:
    """Lista comentários de um problema.

    Args:
        problem_id: ID do problema
    """
    data = _api_get(f"/api/v2/problems/{problem_id}/comments")

    comments = data.get("comments", [])
    if not comments:
        return "Nenhum comentário neste problema."

    lines = [f"**{len(comments)} comentário(s):**\n"]
    for c in comments:
        author = c.get("authorName", "?")
        text = c.get("message", "")
        created = c.get("createdAtTimestamp", "?")
        lines.append(f"- **{author}** ({created}):\n  {text}")

    return "\n".join(lines)


def _severity_color(severity: str) -> str:
    colors = {
        "RESOURCE_CONTENTION": "warning",
        "ERROR": "attention",
        "AVAILABILITY": "attention",
        "PERFORMANCE": "warning",
        "CUSTOM_ALERT": "accent",
    }
    return colors.get(severity, "default")


def _build_adaptive_card(problems: list[dict], title: str) -> dict:
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    facts = []
    for p in problems[:20]:
        severity = p.get("severityLevel", "?")
        impact = p.get("impactLevel", "?")
        facts.append({
            "title": f"[{severity}] {p.get('title', '?')}",
            "value": f"Impacto: {impact} | ID: {p.get('problemId', '?')}",
        })

    card = {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "size": "large",
                        "weight": "bolder",
                        "text": title,
                        "style": "heading",
                    },
                    {
                        "type": "TextBlock",
                        "text": f"{len(problems)} problema(s) | {now}",
                        "isSubtle": True,
                        "spacing": "none",
                    },
                    {
                        "type": "FactSet",
                        "facts": facts,
                    },
                ],
                "actions": [{
                    "type": "Action.OpenUrl",
                    "title": "Abrir Dynatrace",
                    "url": f"{ENV_URL}/#problems",
                }],
            },
        }],
    }
    return card


@mcp.tool()
def notify_teams(
    from_time: str = "now-2h",
    message: str = "",
) -> str:
    """Envia problemas abertos do Dynatrace para o Microsoft Teams via webhook.

    Args:
        from_time: Período de busca (ex: 'now-2h', 'now-1d')
        message: Mensagem adicional opcional para incluir no card
    """
    if not TEAMS_WEBHOOK_URL:
        return "Erro: variável TEAMS_WEBHOOK_URL não configurada."

    data = _api_get(
        "/api/v2/problems",
        params={
            "problemSelector": 'status("OPEN")',
            "from": from_time,
            "to": "now",
        },
    )

    problems = data.get("problems", [])
    if not problems:
        return f"Nenhum problema aberto no período {from_time} → now. Nada enviado."

    title = message if message else "Dynatrace — Problemas Abertos"
    card = _build_adaptive_card(problems, title)

    resp = httpx.post(TEAMS_WEBHOOK_URL, json=card, timeout=15)
    resp.raise_for_status()

    return f"Notificação enviada ao Teams com {len(problems)} problema(s)."


@mcp.tool()
def close_problem(problem_id: str, message: str = "Fechado via MCP") -> str:
    """Fecha um problema no Dynatrace.

    Args:
        problem_id: ID do problema a fechar
        message: Mensagem/motivo do fechamento
    """
    _api_post(f"/api/v2/problems/{problem_id}/close", json={"message": message})
    return f"Problema `{problem_id}` fechado."


if __name__ == "__main__":
    mcp.run()
