# API Contract — Matching Esportivo

Este documento resume os endpoints atuais para integração de Frontend.
Base URL padrão local: `http://localhost:8000`

## Convenção de respostas
- Sucesso (geral):
  - `status` (quando schema inclui)
  - `message` (string)
  - `data` (objeto/lista)
  - `meta` (opcional)
- Erros: `HTTPException` com `detail`.

---

## Health

### `GET /`
- Espera: nada
- Retorna:
```json
{ "app": "Matching Esportivo", "version": "0.1.0", "status": "healthy", "environment": "development|production" }
```

### `GET /health`
- Espera: nada
- Retorna:
```json
{ "status": "healthy", "app": "operational", "database": "connected", "version": "0.1.0" }
```
- Em falha DB: `503`.

### `GET /health/db`
- Espera: nada
- Retorna status PostgreSQL/PostGIS.

### `GET /health/redis`
- Espera: nada
- Retorna status Redis (healthy/disconnected).

---

## Users (`/api/users`)

### `POST /api/users/`
- Body (`UserCreate`):
```json
{
  "email": "user@mail.com",
  "username": "string",
  "full_name": "string",
  "phone": "+5511999999999",
  "avatar_url": "https://...",
  "bio": "string",
  "interests": [
    {
      "sport": "futebol",
      "skill_level": "intermediate",
      "is_primary": true
    }
  ]
}
```
- Retorna: `UserResponse` com usuário criado.

### `GET /api/users/{user_id}`
- Espera: `user_id`
- Retorna: `UserResponse`.

#### Tipos do `UserRead`
- `id`: string
- `email`: string (email válido)
- `username`: string
- `full_name`: string
- `phone`, `avatar_url`, `bio`: string | null
- `is_active`, `is_verified`: bool
- `created_at`, `updated_at`: datetime ISO-8601
- `last_login`: datetime ISO-8601 | null
- `interests`: array de `UserInterestRead`

#### Tipos do `UserInterestRead`
- `id`, `user_id`: string
- `sport`: string
- `skill_level`: string (`beginner|intermediate|advanced`)
- `is_primary`: bool

### `PATCH /api/users/{user_id}`
- Body (`UserUpdate`, parcial): `email`, `username`, `full_name`, `phone`, `avatar_url`, `bio`, `is_active`, `is_verified`.
- Retorna: `UserResponse`.

### `DELETE /api/users/{user_id}`
- Retorna: `UserDeleteResponse`.

### `GET /api/users/?skip=0&limit=20`
- Retorna: `UserListResponse`.

### `GET /api/users/{user_id}/profile`
- Retorna: `UserProfileResponse` com:
  - `user` (`UserRead`)
  - `stats` (`PlayerStatsRead`)

### `PATCH /api/users/me/stats`
- Body (`PlayerStatsUpdate`):
```json
{
  "user_id": "uuid-or-id",
  "position": "atacante",
  "pace": 80,
  "shooting": 78,
  "passing": 70,
  "defense": 50,
  "physical": 75,
  "technique": 82
}
```
- Retorna: `PlayerStatsResponse` (recalcula overall/archetype).

#### Tipos do `PlayerStatsRead`
- `position`: string
- `pace`, `shooting`, `passing`, `defense`, `physical`, `technique`: int (0-100)
- `overall`: int
- `playstyle_archetype`: string

---

## Events (`/api/events`)

### `POST /api/events/`
- Body (`EventCreate`):
```json
{
  "creator_id": "user-id",
  "club_id": "club-id-optional",
  "sport_type": "futebol",
  "scheduled_time": "2026-04-14T18:00:00Z",
  "status": "open",
  "max_participants": 10,
  "latitude": -23.55,
  "longitude": -46.63
}
```
- Retorna: `EventResponse`.

### `GET /api/events/search`
- Query: `latitude`, `longitude`, `radius_km`, `sport_type?`, `limit?`
- Retorna: `EventSearchResponse` com eventos ativos próximos.

### `POST /api/events/{event_id}/join`
- Body:
```json
{ "user_id": "user-id" }
```
- Retorna: `JoinEventResponse` com status `confirmed|waitlist`.

### `GET /api/events/{event_id}/suggestions`
- Retorna: `EventSuggestionsResponse` com jogadores sugeridos.

---

## Clubs (`/api/clubs`)

### `POST /api/clubs/`
- Body (`ClubCreate`):
```json
{
  "name": "Arena X",
  "description": "string",
  "owner_id": "user-id",
  "sport_type": "futebol",
  "privacy_type": "public",
  "latitude": -23.55,
  "longitude": -46.63
}
```
- Retorna: `ClubResponse`.

### `GET /api/clubs/nearby`
- Query: `latitude`, `longitude`, `sport_type?`, `limit?`
- Retorna: `ClubNearbyResponse`.

### `POST /api/clubs/{club_id}/join`
- Body:
```json
{ "user_id": "user-id" }
```
- Retorna: `ClubJoinResponse`.

### `POST /api/clubs/{club_id}/members/{user_id}/approve`
- Body:
```json
{ "reviewer_id": "admin-or-owner-id" }
```
- Retorna: `ClubMembershipReviewResponse`.

### `POST /api/clubs/{club_id}/members/{user_id}/reject`
- Body igual ao approve.
- Retorna: `ClubMembershipReviewResponse`.

---

## Notifications (`/api/notifications`)

### `GET /api/notifications/?user_id={id}&limit=50`
- Retorna: `NotificationListResponse`.

#### Tipos do `NotificationRead`
- `id`, `user_id`: string
- `content`: string
- `type`: `invite|match|event_update`
- `is_read`: bool
- `created_at`: datetime ISO-8601

---

## Feed (`/api/feed`)

### `GET /api/feed/?user_id={id}&radius_km=15&limit=30`
- Retorna: `PersonalizedFeedResponse`.

#### Tipos do `PersonalizedFeedItem`
- `id`, `creator_id`: string
- `club_id`: string | null
- `title`: string
- `sport_type`: string
- `scheduled_time`: datetime ISO-8601
- `status`: `open|full|finished`
- `max_participants`: int
- `distance_km`: number
- `club_priority`: bool
- `confirmed_participants`: int
- `remaining_spots`: int

---

## Ranked (`/api/ranked`)

### `GET /api/ranked/?sport_type=geral&limit=100`
- Retorna: `RankedUsersResponse` ordenado por `mmr` decrescente.

#### Tipos do `RankedUserRead`
- `id`, `user_id`: string
- `full_name`, `username`: string
- `avatar_url`: string | null
- `mmr`: int
- `division`: `bronze|silver|gold|platinum|diamond|immortal|global`
- `league`: string
- `wins`, `losses`: int
- `win_rate`: number
- `sport_type`: string | null
- `position`: string | null
- `overall`: int | null
- `created_at`, `updated_at`: datetime ISO-8601

### `GET /api/ranked/{user_id}`
- Retorna: `UserRankResponse`.

### `POST /api/ranked/match/{winner_id}/{loser_id}`
- Espera: path params.
- Retorna: `UserRankResponse` do vencedor atualizado.

---

## Chat (`/api/chat`)

### `POST /api/chat/rooms/{event_id}`
- Retorna: `ChatRoomResponse`.

### `GET /api/chat/rooms/{room_id}`
- Retorna: `ChatRoomResponse`.

### `POST /api/chat/rooms/{room_id}/messages`
- Body (`ChatMessageCreate`):
```json
{
  "chat_room_id": "room-id",
  "user_id": "user-id",
  "content": "mensagem"
}
```
- Retorna: `ChatMessageResponse`.

#### Tipos do `ChatMessageRead`
- `id`, `chat_room_id`, `user_id`: string
- `content`: string (1-500)
- `created_at`: datetime ISO-8601

### `GET /api/chat/rooms/{room_id}/messages?limit=100`
- Retorna: `ChatMessageListResponse` para polling simples do chat.

---

## Courts (`/api/courts`)

### `POST /api/courts`
- Body (`CourtCreate`):
```json
{
  "owner_id": "user-id",
  "name": "Quadra Centro",
  "description": "string",
  "sport_type": "futsal",
  "latitude": -23.55,
  "longitude": -46.63,
  "price_per_hour": 120,
  "photos_url": ["https://..."]
}
```
- Retorna: `CourtResponse`.

#### Tipos do `CourtRead`
- `price_per_hour`: float
- `photos_url`: array de string

#### Tipos do `BookingRead`
- `status`: string enum (`pending|confirmed|cancelled|completed`)
- `total_price`: float
- `start_time`, `end_time`: datetime ISO-8601

### `GET /api/courts/{court_id}`
- Retorna: `CourtResponse`.

### `POST /api/courts/{court_id}/bookings`
- Body (`BookingCreate`):
```json
{
  "court_id": "court-id",
  "user_id": "user-id",
  "start_time": "2026-04-14T20:00:00Z",
  "end_time": "2026-04-14T22:00:00Z"
}
```
- Retorna: `BookingResponse`.

### `GET /api/courts/{court_id}/availability?start_time=...&end_time=...`
- Retorna:
```json
{ "court_id": "id", "available": true, "start_time": "...", "end_time": "..." }
```

---

## Swagger
- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`
- As descrições atuais estão em Português técnico limpo com alguns trechos em inglês técnico.
