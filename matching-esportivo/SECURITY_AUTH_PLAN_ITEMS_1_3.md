# Plano de Implementação — Autenticação e Autorização Reais (Itens 1–3)

> **Fase:** Segurança (gap estrutural nº 1). Suíte de aceite: `tests/test_security_auth_items_1_3.py`.
>
> **Problema raiz (verificado no código):** a autenticação é um usuário bootstrap único com
> senha em **texto puro** (`app/api/auth.py:36-63,121`); nenhuma rota exige token — o único
> consumo de JWT é no rate-limit de match-performance (`app/middleware/match_performance_rate_limit.py:95`),
> não para autorizar. Logo, hoje há "login" mas **não há AuthN/AuthZ de verdade**.

---

## Item 1 — Hash de senha (nunca texto puro)

| Campo | Conteúdo |
|---|---|
| **Mecanismo** | Hashing lento, com salt, de via única. Opções: `hashlib.scrypt`/`pbkdf2_hmac` (stdlib, sem nova dependência) **ou** reintroduzir `passlib[bcrypt]`/`argon2`. Comparação sempre via `secrets.compare_digest` sobre o hash. |
| **Risco coberto** | Vazamento de senha em texto puro (banco/env/log); ataque offline se o DB vazar; senha adivinhável. |
| **Prioridade** | **P0 (crítico)** — primeiro passo, pois destrava o Item 2. |
| **Como fazer** | 1. Em `app/core/security.py`, criar `hash_password(password: str) -> str` e `verify_password(password: str, hashed: str) -> bool`. 2. Substituir a comparação `secrets.compare_digest(request.password, user.password)` por `verify_password(request.password, user.hashed_password)`. 3. Para o usuário seed (dev), gerar o hash (não guardar senha). 4. Cobrir com os testes do Item 1. |
| **Arquitetura** | `app/core/security.py` (camada pura, testável) é a única fonte de hashing; `app/api/auth.py` apenas chama `verify_password`. Nenhum hash é construído no controller. |

---

## Item 2 — Login ligado ao modelo `User` real

| Campo | Conteúdo |
|---|---|
| **Mecanismo** | Autenticar contra a tabela `User` (`app/models/user.py`) por e-mail; verificar hash; emitir token com `user_id` real. Substituir `_bootstrap_user()` (mantendo, no máximo, um seed de desenvolvimento). |
| **Risco coberto** | Autenticação fake de usuário único → sem multi-usuário, sem conta real; o `User`/`create_user` existentes ficam órfãos da autenticação. |
| **Prioridade** | **P0** |
| **Como fazer** | 1. Adicionar/usar campo `hashed_password` no modelo `User`. 2. Criar `authenticate_user(session, email, password) -> User \| None` em `app/services/user_service.py` (busca por email + `verify_password`; erro sempre genérico `invalid_credentials`). 3. `POST /api/auth/login` passa a consultar o DB e emite token com `sub=user.id`. 4. Tratar timing: mesmo caminho para usuário inexistente vs senha errada. |
| **Arquitetura** | `auth.py` (controller) → `user_service.authenticate_user` (serviço) → `security.verify_password` (hash). Token: `sub`=id, `user_id`=id. |

---

## Item 3 — Dependência de autorização por rota

| Campo | Conteúdo |
|---|---|
| **Mecanismo** | Dependência FastAPI `require_user` que lê `Authorization: Bearer`, decodifica (reaproveitar `app/core/security.py:decode_jwt_subject_from_header`, que já existe) e injeta a identidade; aplicar `Depends(require_user)` nas rotas que exigem identidade. |
| **Risco coberto** | Endpoints abertos → acesso indevido a dados/ações de outros (IDOR), mutações não autenticadas, vazamento de feed/notificações. |
| **Prioridade** | **P0** (na prática é o objetivo central desta fase). |
| **Como fazer** | 1. Criar `app/api/deps.py` com `require_user(authorization: str = Header(...)) -> str`. 2. Mapear **públicas** (health, listagem de eventos/ranking, login/refresh) vs **privadas** (`users/me`, `clubs/{id}/join`, `events` (POST/PUT), `notifications`, `feed`, `chat`, `court` de criação/reserva). 3. Aplicar `Depends(require_user)` nas privadas. 4. Teste de contrato: cada rota sensível exige token; 401 sem token/ inválido. |
| **Arquitetura** | `app/api/deps.py` (dependência FastAPI) → `security.decode_jwt_subject_from_header`; routers declaram a dependência. Identidade trafega por injeção, não por parse manual em cada rota. |

---

## Ordem de execução e critério de aceite

1. **Item 1** → `hash_password`/`verify_password` verdes.
2. **Item 2** → login autentica contra `User`; senha nunca comparada em claro.
3. **Item 3** → rotas privadas exigem `require_user`; públicas documentadas.

**Aceite final:** `pytest -q tests/test_security_auth_items_1_3.py` sem skips pendentes nos 3 itens + suíte geral 0 failed.
