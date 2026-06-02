# Dynatrace MCP Server

Servidor [MCP](https://modelcontextprotocol.io) que conecta **Cursor**, **Claude Code** e outros clientes MCP ao **Dynatrace** para monitorar e gerenciar problemas de infraestrutura e serviços.

## Funcionalidades

- `list_problems` — Lista problemas abertos/fechados por período
- `get_problem` — Detalhes de um problema (entidades afetadas, evidências, management zones)
- `get_problem_comments` — Comentários de um problema
- `notify_teams` — Envia problemas abertos para o Microsoft Teams via webhook
- `close_problem` — Fecha um problema com mensagem

## Pré-requisitos

- Python 3.10+
- Git
- Token Dynatrace com `problems.read` e `problems.write` (para fechar problemas)
- *(Opcional)* Webhook do Microsoft Teams

## Instalação

### Linux / macOS

```bash
git clone https://github.com/jorgealcinoneto/dynatrace-mcp.git ~/dev/dynatrace-mcp
cd ~/dev/dynatrace-mcp

pip3 install "mcp[cli]" httpx

export DYNATRACE_ENV_URL="https://SEU-AMBIENTE.live.dynatrace.com"
export DYNATRACE_API_TOKEN="dt0c01.XXXXX..."
export TEAMS_WEBHOOK_URL="https://xxx.webhook.office.com/..."
```

Persistir variáveis em `~/.bashrc` ou `~/.zshrc`.

### Windows (PowerShell)

```powershell
git clone https://github.com/jorgealcinoneto/dynatrace-mcp.git $env:USERPROFILE\dev\dynatrace-mcp
cd $env:USERPROFILE\dev\dynatrace-mcp

python -m pip install "mcp[cli]" httpx

$env:DYNATRACE_ENV_URL = "https://SEU-AMBIENTE.live.dynatrace.com"
$env:DYNATRACE_API_TOKEN = "dt0c01.XXXXX..."
$env:TEAMS_WEBHOOK_URL = "https://xxx.webhook.office.com/..."

setx DYNATRACE_ENV_URL "https://SEU-AMBIENTE.live.dynatrace.com"
setx DYNATRACE_API_TOKEN "dt0c01.XXXXX..."
setx TEAMS_WEBHOOK_URL "https://xxx.webhook.office.com/..."
```

> **Dica:** se `python` não for reconhecido, instale em [python.org](https://www.python.org/downloads/) com **Add Python to PATH** ou use `py -3` no lugar de `python`.

### Token de API (Dynatrace)

Gere um token no Dynatrace com as permissões:

- `problems.read`
- `problems.write` (para fechar problemas)

Em: **Settings > Integration > Dynatrace API > Generate token**

### Webhook do Teams

1. No Teams, abra o canal onde quer receber alertas
2. Clique em **...** > **Workflows** > **Post to a channel when a webhook request is received**
3. Copie a URL gerada e configure em `TEAMS_WEBHOOK_URL`

## Registrar no Cursor

Adicione em `~/.cursor/mcp.json` (Linux/macOS) ou `%USERPROFILE%\.cursor\mcp.json` (Windows):

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

Exemplo Windows (`cwd`):

```json
"cwd": "C:\\Users\\SEU_USUARIO\\dev\\dynatrace-mcp",
"command": "python"
```

Reinicie o Cursor após salvar.

## Registrar no Claude Code

```bash
claude mcp add dynatrace -- python3 ~/dev/dynatrace-mcp/server.py
```

Windows:

```powershell
claude mcp add dynatrace -- python "$env:USERPROFILE\dev\dynatrace-mcp\server.py"
```

Ou adicione manualmente ao `~/.claude/.mcp.json` (mesma estrutura do Cursor acima).

## Uso

```
> liste os problemas abertos no dynatrace
> detalhes do problema P-12345678
> avise no teams sobre os problemas abertos
> feche o problema P-12345678 com mensagem "resolvido após deploy"
```
