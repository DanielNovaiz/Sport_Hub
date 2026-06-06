# 🏗️ Arquitetura do Sistema - Matching Esportivo

> Estado atual do repositório: backend FastAPI em Python e frontend mobile em Flutter/Dart. O diagrama abaixo reflete uma visão histórica/objetivo e não um frontend web React já implementado neste workspace.

## 1. Diagrama de Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER (Fase 3)                  │
├──────────────────────────────┬──────────────────────────────────┤
│     Web (React/TypeScript)   │    Mobile (React Native)         │
└────────────────┬─────────────┴──────────────────┬───────────────┘
                 │ HTTP/HTTPS                     │ HTTP/HTTPS
                 └────────────────┬────────────────┘
                                  │
┌─────────────────────────────────▼─────────────────────────────────┐
│                       API LAYER (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  /api/events │  │ /api/athletes│  │/api/matching │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│         │                │                     │                  │
│  [Router Events]   [Router Athletes]   [Router Matching]          │
└────────────┬─────────────┬──────────────────┬──────────────────────┘
             │             │                  │
       (Dependency Injection - Pydantic + Validation)
             │             │                  │
┌────────────▼─────────────▼──────────────────▼──────────────────────┐
│                 SERVICE LAYER (Business Logic)                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────┐ │
│  │ Matching Service │  │  EventService    │  │ AthleteService    │ │
│  │  - Find nearby   │  │  - CRUD          │  │  - Profile mgmt   │ │
│  │  - Score calc    │  │  - Validate      │  │  - Auth  (Fase 2) │ │
│  └──────────────────┘  └──────────────────┘  └───────────────────┘ │
└────────────┬─────────────┬──────────────────┬──────────────────────┘
             │             │                  │
             └─────────────┼──────┬───────────┘
                           │      │
        ┌──────────────────┘      └─────────────────┐
        │                                            │
┌───────▼────────────────┐           ┌──────────────▼──────────────┐
│   PERSISTENCE LAYER    │           │    CACHE & MESSAGING LAYER   │
│    (SQLAlchemy ORM)    │           │        (Redis)               │
│  ┌────────────────────┐│           │  ┌─────────────────────────┐ │
│  │  Models            ││           │  │ Cache (Popular events)  │ │
│  │  - Event           ││           │  │ Cache (User sessions)   │ │
│  │  - Athlete         ││           │  │ Queue (Notifications)   │ │
│  │  - Rating (Fase 2) ││           │  │ PubSub (WebSocket)      │ │
│  └────────────────────┘│           │  └─────────────────────────┘ │
│  ┌────────────────────────────────┐│                              │
│  │   Query Layer (PostGIS)         ││  Redis 7 (Async)            │
│  │   - ST_DWithin (proximity)      ││                              │
│  │   - ST_Distance (ordering)      ││                              │
│  │   - GIST Indexes (performance)  ││                              │
│  └────────────────────────────────┘│                              │
└─────────────────────────────────────┴──────────────────────────────┘
        │                                    │
        │                                    │
┌───────▼──────────────────────────┐  ┌─────▼──────────────────────┐
│    PostgreSQL 16 + PostGIS       │  │  Docker Compose Network     │
│  ┌──────────────────────────────┐│  │  ┌─────────────────────────┐│
│  │  Database: matching_db       ││  │  │ matching_network (bridge)││
│  │  Tables:                     ││  │  │ - postgres              ││
│  │  - event                     ││  │  │ - redis                 ││
│  │  - athlete                   ││  │  │ - pgadmin (dev only)    ││
│  │  - rating (Fase 2)           ││  │  │                         ││
│  │  Indexes:                    ││  │  └─────────────────────────┘│
│  │  - idx_event_location (GIST) ││  │  Volumes:                   │
│  │  - idx_athlete_created_at    ││  │  - postgres_data            │
│  │  - idx_event_status          ││  │  - redis_data               │
│  └──────────────────────────────┘│  └─────────────────────────────┘
│  Replication: ✗ (Fase 3)          │
│  Backup: ✗ (Fase 3)               │
└───────────────────────────────────┘
```

## 2. Fluxo de Matching de Eventos

```
┌─────────────────────────────────────────────────────────────┐
│ USUARIO BUSCA EVENTOS PRÓXIMOS                              │
│ POST /api/events/search/nearby                              │
└──────────────────────────────┬────────────────────────────────┘
                               │
                 ┌─────────────▼──────────────┐
                 │  Validação (Pydantic)      │
                 │ - Lat/Lng: [-90, 90]      │
                 │ - Radius: [1, 100] km     │
                 │ - Sport: string            │
                 └──────────────┬──────────────┘
                                │
                 ┌──────────────▼───────────────┐
                 │ Matching Service             │
                 │ find_events_nearby()         │
                 └──────────────┬───────────────┘
                                │
         ┌──────────────────────▼──────────────────────┐
         │ Construir Query PostGIS/SQLAlchemy           │
         │                                              │
         │ distance_degrees = radius_km / 111.32       │
         │                 = 15 / 111.32               │
         │                 ≈ 0.1349°                  │
         │                                              │
         │ query = SELECT * FROM event                 │
         │ WHERE ST_DWithin(location, user_point,      │
         │                 0.1349)  ◄─ Índice GIST!    │
         │ AND sport = ?                               │
         │ AND status = 'open'                         │
         │ ORDER BY ST_Distance(...) * 111.32          │
         │ LIMIT 20                                     │
         └──────────────┬──────────────────────────────┘
                        │
            ┌───────────▼────────────┐
            │ Executar em PostgreSQL │
            │ Usar índice GIST       │
            │ Complexity: O(log n)   │
            └───────────┬────────────┘
                        │
         ┌──────────────▼─────────────────┐
         │ Calcular Match Scores          │
         │ (para cada evento encontrado)  │
         │                                 │
         │ score = w_s * sport_match +    │
         │         w_h * skill_harmony    │
         │                                 │
         │ Range: [0.0, 1.0]              │
         └──────────────┬─────────────────┘
                        │
        ┌───────────────▼────────────────┐
        │ Ordenar por Score + Distância  │
        │ (match score DESC,             │
        │  distance ASC)                 │
        └───────────────┬────────────────┘
                        │
        ┌───────────────▼────────────────┐
        │ Serializar com Pydantic        │
        │ (Event → EventResponse)        │
        └───────────────┬────────────────┘
                        │
        ┌───────────────▼────────────────┐
        │ Cache em Redis                 │
        │ (TTL: 5 minutos)  [Fase 2]     │
        │ Key: search:{lat}:{lng}:{r}    │
        └───────────────┬────────────────┘
                        │
                        ▼
        ┌──────────────────────────────┐
        │ Retornar JSON (HTTP 200)     │
        │ [                            │
        │   {                          │
        │     "id": "...",             │
        │     "title": "Futsal ...",   │
        │     "distance_km": 2.3,      │
        │     "match_score": 0.95      │
        │   },                         │
        │   ...                        │
        │ ]                            │
        └──────────────────────────────┘
```

## 3. Stack de Depdências

```
┌────────────────────────────────────────────────────────────┐
│                    APLICAÇÃO (Python 3.11)                 │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ WEB FRAMEWORK                                       │   │
│  │ ✓ FastAPI (0.104) - Async REST API                │   │
│  │ ✓ Uvicorn - ASGI Server                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ DATA VALIDATION & SERIALIZATION                     │   │
│  │ ✓ Pydantic 2.0 - Request/Response validation       │   │
│  │ ✓ Pydantic Settings - Config management            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ASYNC DATABASE ACCESS                              │   │
│  │ ✓ SQLAlchemy 2.0 - ORM & Query builder             │   │
│  │ ✓ SQLModel - Models with Pydantic                  │   │
│  │ ✓ GeoAlchemy2 - PostGIS integration                │   │
│  │ ✓ psycopg2-binary - PostgreSQL driver              │   │
│  │ ✓ Alembic - Database migrations  [Fase 2]          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ CACHE & MESSAGING                                  │   │
│  │ ✓ Redis (client) - Async support  [Fase 2]        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ AUTHENTICATION & SECURITY                           │   │
│  │ ✓ PyJWT - JWT tokens  [Fase 2]                     │   │
│  │ ✓ python-jose - JOSE support  [Fase 2]            │   │
│  │ ✓ Passlib - Password hashing  [Fase 2]            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ TESTING                                             │   │
│  │ ✓ Pytest - Testing framework                       │   │
│  │ ✓ pytest-asyncio - Async test support              │   │
│  │ ✓ pytest-cov - Coverage reporting                  │   │
│  │ ✓ HTTPx - Async HTTP client                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ CODE QUALITY                                        │   │
│  │ ✓ Black - Code formatter                           │   │
│  │ ✓ Flake8 - Linter                                  │   │
│  │ ✓ isort - Import sorting                           │   │
│  │ ✓ MyPy - Type checking                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ UTILITIES                                           │   │
│  │ ✓ python-dotenv - .env file support                │   │
│  │ ✓ pytz - Timezone handling                         │   │
│  │ ✓ requests - HTTP client library                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

## 4. Modelo de Dados - Relações

```
EVENT (Tabela Principal)
┌──────────────────────────────────────────────────┐
│ id (PK)                                          │
│ title                                            │
│ description                                      │
│ sport                                            │
│ skill_level                                      │
│ location ──────────┐ (POINT - PostGIS)          │
│ latitude           │                             │
│ longitude          │                             │
│ address            │                             │
│ scheduled_date     │                             │
│ duration_minutes   │                             │
│ max_participants   │                             │
│ current_participants                             │
│ organizer_id (FK) ──┐                           │
│ status (indexed)    │                           │
│ created_at (indexed)│                           │
│ updated_at          │                           │
│ tags (JSON)         │                           │
└──────────────────────────────────────────────────┘
        │                   │
        │                   │
    (Fase 2)            (Fase 2)
        │                   │
        ▼                   ▼
    (FK: organizer_id)   (FK: EVENT)
        │                   │
        │                   ▼
        │            RATING (Tabela Nova)
        │            ┌──────────────────┐
        │            │ id (PK)          │
        │            │ event_id (FK)    │
        │            │ athlete_id (FK)  │
        │            │ score (0-5)      │
        │            │ comment          │
        │            │ created_at       │
        │            └──────────────────┘
        │
        ▼
    ATHLETE (Tabela Nova)
    ┌──────────────────────────────┐
    │ id (PK)                      │
    │ email (unique)               │
    │ username (unique)            │
    │ full_name                    │
    │ phone                        │
    │ avatar_url                   │
    │ latitude (last location)    │
    │ longitude (last location)   │
    │ preferred_sports (JSON)      │
    │ skill_levels (JSON)          │
    │ search_radius_km             │
    │ is_active                    │
    │ is_verified                  │
    │ created_at (indexed)         │
    │ updated_at                   │
    │ last_login                   │
    └──────────────────────────────┘
```

## 5. Database - Índices e Performance

```
ÍNDICES ATUAL (Fase 1):
├─ PRIMARY KEY idx_event_id (BTREE)
├─ UNIQUE idx_athlete_email (BTREE)  [Fase 2]
├─ SPATIAL idx_event_location (GIST)
│   └─ Para ST_DWithin() - Proximity search
├─ REGULAR idx_event_status (BTREE)
│   └─ Para filtrar por 'open'
├─ REGULAR idx_event_created_at (BTREE)
│   └─ Para ordenação por data
└─ REGULAR idx_athlete_created_at (BTREE) [Fase 2]

ÍNDICES FUTUROS (Fase 2+):
├─ COMPOSITE (sport, skill_level, status)
├─ COVERING INDEX para cached fields
└─ PARTITIONING por status para grandes volumes
```

## 6. Fluxo CI/CD (Roadmap - Fase 3)

```
Desenvolvimento Local
    │
    ├─ git push → GitHub
    │
    ▼
GitHub Actions
    │
    ├─ [1] Lint & Format
    │       └─ Black, Flake8, MyPy
    │
    ├─ [2] Unit Tests
    │       └─ pytest --cov=app (target: 80%+)
    │
    ├─ [3] Security Scan
    │       └─ Bandit, OWASP checks
    │
    ├─ [4] Build Docker Image
    │       └─ docker build -t matching-esportivo:$SHA
    │
    └─ [5] Deploy to Staging
            └─ Docker Compose on AWS EC2
    
Manual Review (QA)
    │
    ▼ Approval
    │
Deploy to Production
    │
    ├─ Health Checks
    ├─ Database Migrations (Alembic)
    ├─ Smoke Tests
    └─ Monitor logs/metrics
```

---

## Resumo da Arquitetura

✅ **Camadas** (Separation of Concerns):
- API Layer (FastAPI routers)
- Service Layer (business logic)
- Persistence Layer (SQLAlchemy ORM)
- Cache/Message Layer (Redis)

✅ **Banco de Dados**:
- PostgreSQL 16 + PostGIS para queries geoespaciais O(log n)
- Índices GIST otimizados para ST_DWithin
- Modelagem relacional normalizada

✅ **Async Throughout**:
- FastAPI com async handlers
- SQLAlchemy async engine
- Redis async client

✅ **Validação em Múltiplas Camadas**:
- Pydantic (request/response)
- SQLModel (database constraints)
- Business logic (services)

✅ **Pronto para Scale**:
- Índices apropriados
- Query optimization
- Caching layer
- Async-first implementation
