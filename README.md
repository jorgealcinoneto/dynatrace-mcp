# Dynatrace MCP Server

Servidor MCP que conecta o Claude Code ao Dynatrace para monitorar e gerenciar problemas de infraestrutura e serviços.

## Funcionalidades

- `list_problems` — Lista problemas abertos/fechados por período
- `get_problem` — Detalhes de um problema (entidades afetadas, evidências, management zones)
- `get_problem_comments` — Comentários de um problema
- `notify_teams` — Envia problemas abertos para o Microsoft Teams via webhook
- `close_problem` — Fecha um problema com mensagem

## Instalação

```bash
# 1. Clonar o repositório
git clone <url-do-repo> ~/dev/dynatrace-mcp
cd ~/dev/dynatrace-mcp

# 2. Instalar dependências
pip3 install mcp[cli] httpx --break-system-packages

# 3. Configurar variáveis de ambiente (adicionar ao ~/.zshrc ou ~/.bashrc)
export DYNATRACE_ENV_URL="https://SEU-AMBIENTE.live.dynatrace.com"
export DYNATRACE_API_TOKEN="dt0c01.XXXXX..."
export TEAMS_WEBHOOK_URL="https://xxx.webhook.office.com/..."
```

### Token de API (Dynatrace)

Gere um token no Dynatrace com as permissões:

- `problems.read`
- `problems.write` (para fechar problemas)

Em: **Settings > Integration > Dynatrace API > Generate token**

### Webhook do Teams

1. No Teams, abra o canal onde quer receber alertas
2. Clique em **...** > **Workflows** > **Post to a channel when a webhook request is received**
3. Copie a URL gerada e configure em `TEAMS_WEBHOOK_URL`

## Registrar no Claude Code

```bash
claude mcp add dynatrace -- python3 ~/dev/dynatrace-mcp/server.py
```

Ou adicione manualmente ao `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "dynatrace": {
      "command": "python3",
      "args": ["server.py"],
      "cwd": "/caminho/para/dynatrace-mcp",
      "env": {
        "DYNATRACE_ENV_URL": "https://SEU-AMBIENTE.live.dynatrace.com",
        "DYNATRACE_API_TOKEN": "dt0c01.XXXXX...",
        "TEAMS_WEBHOOK_URL": "https://xxx.webhook.office.com/..."
      }
    }
  }
}
```

## Uso no Claude Code

```
> liste os problemas abertos no dynatrace
> detalhes do problema P-12345678
> avise no teams sobre os problemas abertos
> feche o problema P-12345678 com mensagem "resolvido após deploy"
```
