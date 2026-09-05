# Pendência — Item 3 (Autorização por rota) — escopo restante

> Status: `require_user` aplicado em `notifications`, `feed`, `chat`, `clubs`
> (create/join/approve/reject) e `users/me/stats`. Falta cobrir `events` e `court`.

## Por que pendente
O Item 3 foi aplicado ao lote com testes de API existentes. `events` e `court`
não têm teste de API hoje; a aplicação ficou para um follow-up controlado.

## Endpoints que devem passar a exigir `Depends(require_user)`

**`app/api/events.py`** (mutations — exigem identidade):
- `POST /api/events/` (criar evento) → `_auth: str = Depends(require_user)`
- `POST /api/events/{event_id}/join` (participar) → `_auth`

Permanecem **públicos** (leitura): `GET /api/events/search`,
`GET /api/events/{event_id}/suggestions` (avaliar necessidade de auth no futuro).

**`app/api/court.py`** (mutations/pessoais):
- `POST /api/courts` (criar quadra) → `_auth`
- `POST /api/courts/{court_id}/bookings` (reservar) → `_auth`
- `GET /api/courts/bookings/my` (minhas reservas) → `_auth`

Permanecem **públicos**: `GET /api/courts`, `GET /api/courts/{court_id}`,
`GET /api/courts/{court_id}/availability`.

## Como fazer
1. Em cada endpoint acima: `from app.api.deps import require_user` + parâmetro
   `_auth: str = Depends(require_user)`.
2. Sempre que a rota receber `user_id` no corpo/query, **substituir pela
   identidade do token** (subject) — nunca confiar em id enviado pelo cliente.
3. Rodar `pytest -q` (esperado 0 failed) e, se houver teste de API novo,
   gerar token via `encode_access_token`.

## Critério de aceite
Requisições sem `Authorization` (ou com token inválido) → `401`; rotas públicas
continuam acessíveis sem token.
