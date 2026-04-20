# Matching Esportivo

API FastAPI para matchmaking esportivo com foco em geolocalização, performance e evolução de atletas.

## Stack

- Python + FastAPI
- PostgreSQL + PostGIS
- Redis
- SQLAlchemy/SQLModel (async)

## Como rodar

1. Configure ambiente:
   - copie `.env.example` para `.env`
   - preencha variáveis necessárias
2. Suba infraestrutura (Postgres/Redis) com Docker Compose
3. Instale dependências Python
4. Inicie a API por `main.py`

## Endpoints principais

- `GET /health`
- `GET /metrics`
- `POST /api/events`
- `GET /api/events/{id}`
- `GET /api/events`
- `POST /api/events/search/nearby`

## Estrutura principal

- `main.py` — bootstrap da aplicação e middlewares
- `app/api/` — rotas
- `app/services/` — regras de negócio
- `app/models/` — modelos de dados
- `app/schemas/` — contratos de entrada/saída
- `app/core/` — configuração e banco

## Documentação adicional

- `SETUP.md`
- `ARCHITECTURE.md`
- `CONVENTIONS.md`
- `MATHEMATICS.md`
- `QUICKREF.md`
- `INDEX.md`

## Status

Base organizada e pronta para continuidade das próximas fases.
