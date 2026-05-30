import os

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dynatrace")

ENV_URL = os.environ.get("DYNATRACE_ENV_URL", "").rstrip("/")
API_TOKEN = os.environ.get("DYNATRACE_API_TOKEN", "")

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
