# Plano de Implementação — Hardening (Itens 4–6)

> **Fase:** Segurança (reforços de segunda ordem). Suíte de aceite: `tests/test_security_hardening_items_4_6.py`.
>
> Pré-requisito lógico: Itens 1–3 (auth real) implementados. Estes itens endurecem token,
> brute-force e exposição de informação.

---

## Item 4 — Hardening do JWT

| Campo | Conteúdo |
|---|---|
| **Mecanismo** | Claims padrão + validação: `iat`, `aud`, `iss`; distinguir `type` (`access`/`refresh`) e **exigir** `type=="access"` no decode de acesso; refresh com rotação (novo refresh a cada uso) **ou** prazo menor + revogação via Redis (que já existe em `app/core/redis.py`). |
| **Risco coberto** | Refresh reutilizável/roubado por 7 dias (`auth.py:98-105`); refresh usado como access (sem checagem de `type` no caminho de acesso); falta de audiência/emissor facilita confusão de tokens entre ambientes. |
| **Prioridade** | **P1** |
| **Como fazer** | 1. Padronizar payload com `iat`, `aud`, `iss`, `type`, `jti`. 2. Criar `decode_access_token` que valida assinatura + `type` + expiração + `aud`. 3. No refresh, emitir novo par e invalidar o antigo (blacklist `jti` no Redis com TTL). 4. Ajustar `decode_jwt_subject_from_header` para usar o decode tipado. |
| **Arquitetura** | `app/core/security.py` (encode/decode com claims) + `app/core/redis.py` para revogação. `auth.py` só emite/rotaciona. |

---

## Item 5 — Rate limit específico em `/api/auth/*`

| Campo | Conteúdo |
|---|---|
| **Mecanismo** | Throttle por IP (e por e-mail) para login/refresh, com janela + burst; resposta `429`; mensagem genérica (sem distinguir usuário existente). |
| **Risco coberto** | Brute-force de credenciais em `/api/auth/login` (hoje só há limite global de 20 r/s no nginx + throttle de match-performance, nenhum para auth). |
| **Prioridade** | **P1** |
| **Como fazer** | 1. Criar `app/core/rate_limit.py` com `is_rate_limited(key, limit, window)` usando `INCR`/`EXPIRE` no Redis. 2. Aplicar via dependência/middleware no router de auth (janela ex.: 5 tentativas/min por IP+email). 3. Retornar `429 Too Many Requests` com corpo neutro. |
| **Arquitetura** | `app/core/rate_limit.py` (Redis) ← `app/api/deps.py`/middleware ← router de auth. |

---

## Item 6 — Sanitizar healthchecks

| Campo | Conteúdo |
|---|---|
| **Mecanismo** | Respostas de `/health`, `/health/db`, `/health/redis` sem detalhe interno; apenas status booleano + versão pública; o erro real vai para o log (`logger.error`), não para a resposta. |
| **Risco coberto** | Info disclosure: `"error": str(e)` (`main.py:170,222,243`) expõe host do DB, versão PostGIS, mensagens de exceção. |
| **Prioridade** | **P2** |
| **Como fazer** | 1. Remover `"error": str(e)` dos retornos 503. 2. Logar `logger.error(..., exc_info=True)` e devolver `{"status":"unhealthy", "app":..., "database":"disconnected"}` sem detalhes. 3. Ajustar teste de aceite para exigir ausência de campo `error`. |
| **Arquitetura** | Endpoints `/health*` devolvem contrato mínimo; detalhe fica no log estruturado. |

---

## Ordem de execução e critério de aceite

1. **Item 4** → decode tipado + rotação/revogação de refresh.
2. **Item 5** → `429` após N tentativas no login.
3. **Item 6** → health sem campo `error`.

**Aceite final:** `pytest -q tests/test_security_hardening_items_4_6.py` sem skips pendentes + suíte geral 0 failed.
