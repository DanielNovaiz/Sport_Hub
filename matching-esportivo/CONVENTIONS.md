# Convenções — Matching Esportivo

Guia de padronização para execução rápida e legibilidade por IA.

## 1) Nomenclatura

- **snake_case**: funções, variáveis, módulos, arquivos Python
- **CamelCase**: classes
- **UPPER_SNAKE_CASE**: constantes

Exemplos:

```python
nearby_event_search_query = ...

class EventNearbySearch(BaseModel):
    ...

MAX_NEARBY_RADIUS_KM = 100.0
```

Regras:

- nomes explícitos e sem ambiguidade
- evitar abreviações vagas
- preferir nomes longos e claros a nomes curtos e opacos

## 2) Estrutura de resposta da API

Padrão JSON único:

```json
{
  "status": "success",
  "message": "operation completed",
  "data": {},
  "meta": {}
}
```

Padrão de erro:

```json
{
  "status": "error",
  "message": "invalid payload",
  "data": null,
  "meta": {
    "field": "latitude"
  }
}
```

Contrato:

- `status`: `success` | `error`
- `message`: curto e objetivo
- `data`: payload principal
- `meta`: paginação, contadores ou contexto adicional

## 3) Regra de commits

Formato curto e grosso:

```text
feat: add nearby event search
fix: correct postgis radius query
refactor: simplify event service
test: add user schema validation tests
docs: update api response conventions
```

Prefixos válidos:

- `feat:`
- `fix:`
- `refactor:`
- `test:`
- `chore:`
- `docs:`

Regras:

- uma linha objetiva
- descrever mudança concreta
- sem narrativa longa

## 4) Regra de ouro

- Proibido código comentado. Se não serve, delete.
- Proibido função com mais de 30 linhas.
- Se passou de 30 linhas, quebrar em funções menores.
- Comentário não substitui nome claro ou design simples.

## 5) Regras técnicas obrigatórias

- Type hints em 100% do código Python
- Pydantic V2 para entrada e saída
- FastAPI sempre async
- PostGIS para lógica espacial
- Redis para pub/sub e fluxos não bloqueantes
- Service layer para lógica de negócio
- SQL interpolado manualmente é proibido

## 6) Critério de decisão

Em dúvida entre duas implementações, escolher:

1. mais simples
2. mais tipada
3. mais fácil de corrigir
4. mais isolada por arquivo

Objetivo final: código funcional, substituível e pronto para produção no menor tempo possível.


MAX_NEARBY_RADIUS_KM = 100.0
```

Regras:

- nomes explícitos e sem ambiguidade
- evitar abreviações vagas
- preferir nomes longos e claros a nomes curtos e opacos

## 2) Estrutura de resposta da API

Padrão JSON único:

```json
{
  "status": "success",
  "message": "operation completed",
  "data": {},
  "meta": {}
}
```

Padrão de erro:

```json
{
  "status": "error",
  "message": "invalid payload",
  "data": null,
  "meta": {
    "field": "latitude"
  }
}
```

Contrato:

- `status`: `success` | `error`
- `message`: curto e objetivo
- `data`: payload principal
- `meta`: paginação, contadores ou contexto adicional

## 3) Regra de commits

Formato curto e grosso:

```text
feat: add nearby event search
fix: correct postgis radius query
refactor: simplify event service
test: add user schema validation tests
docs: update api response conventions
```

Prefixos válidos:

- `feat:`
- `fix:`
- `refactor:`
- `test:`
- `chore:`
- `docs:`

Regras:

- uma linha objetiva
- descrever mudança concreta
- sem narrativa longa

## 4) Regra de ouro

- Proibido código comentado. Se não serve, delete.
- Proibido função com mais de 30 linhas.
- Se passou de 30 linhas, quebrar em funções menores.
- Comentário não substitui nome claro ou design simples.

## 5) Regras técnicas obrigatórias

- Type hints em 100% do código Python
- Pydantic V2 para entrada e saída
- FastAPI sempre async
- PostGIS para lógica espacial
- Redis para pub/sub e fluxos não bloqueantes
- Service layer para lógica de negócio
- SQL interpolado manualmente é proibido

## 6) Critério de decisão

Em dúvida entre duas implementações, escolher:

1. mais simples
2. mais tipada
3. mais fácil de corrigir
4. mais isolada por arquivo

Objetivo final: código funcional, substituível e pronto para produção no menor tempo possível.


### Exemplos

```python
nearby_event_search_query = ...

class EventNearbySearch(BaseModel):
    ...

MAX_NEARBY_RADIUS_KM = 100.0
```

### Regras

- nomes devem ser explícitos
- evite abreviações vagas
- prefira nomes que expliquem o papel do dado

---

## 2. Estrutura de resposta da API

### Padrão JSON

```json
{
  "status": "success",
  "message": "operation completed",
  "data": {},
  "meta": {}
}
```

### Regras

- `status`: `success` ou `error`
- `message`: curto e objetivo
- `data`: payload principal
- `meta`: paginação, contadores ou contexto extra

### Erro padrão

```json
{
  "status": "error",
  "message": "invalid payload",
  "data": null,
  "meta": {
    "field": "latitude"
  }
}
```

---

## 3. Regra de commits

### Formato

```text
feat: add nearby event search
fix: correct postgis radius query
refactor: simplify event service
```

### Prefixos permitidos

- `feat:` nova funcionalidade
- `fix:` correção
- `refactor:` reorganização sem mudar comportamento
- `test:` testes
- `chore:` manutenção
- `docs:` documentação

### Regras

- commit curto
- sem texto longo
- descreva a mudança, não a história

---

## 4. Regra de ouro

- Proibido código comentado. Se não serve, delete.
- Proibido função com mais de 30 linhas.
- Se a função passou de 30 linhas, divida.
- Comentário não substitui nome claro ou estrutura boa.

### Leitura prática

- código comentado = ruído
- função longa = risco de bug
- função pequena = IA corrige mais rápido

---

## 5. Regras adicionais

- Pydantic V2 para entrada e saída.
- FastAPI sempre com handlers `async`.
- PostGIS para lógica espacial.
- Redis para pub/sub e tarefas assíncronas.
- Service layer para regra de negócio.
- SQL interpolado manualmente é proibido.

---

## 6. Critério de qualidade

Se houver dúvida entre duas opções, escolha:

1. a mais simples
2. a mais tipada
3. a mais fácil de corrigir
4. a que reduz arquivos tocados no futuro

O objetivo é manter o sistema rápido de evoluir e fácil de substituir.
## Dicionário de padronização

Este arquivo define regras objetivas. Se o código não seguir isto, está fora do padrão.

---

## Padrão de nomenclatura

### Python

- **snake_case** para funções, variáveis, módulos e arquivos.
- **CamelCase** para classes.
- **UPPER_SNAKE_CASE** para constantes.

### Exemplos

```python
nearby_event_search_query = ...

class EventNearbySearch(BaseModel):
    ...

MAX_NEARBY_RADIUS_KM = 100.0
```

### Regras diretas

- nomes devem ser explícitos
- evite abreviações vagas
- prefira `user_preferred_sports` a `prefs`

---

## Estrutura de resposta da API

### Padrão JSON

Respostas devem ser previsíveis e estáveis.

```json
{
  "status": "success",
  "message": "operation completed",
  "data": {},
  "meta": {}
}
```

### Regras

- `status`: `success` | `error`
- `message`: curto e objetivo
- `data`: payload principal
- `meta`: paginação, contadores ou contexto extra

### Erros

```json
{
  "status": "error",
  "message": "invalid payload",
  "data": null,
  "meta": {
    "field": "latitude"
  }
}
```

---

## Regra de commits

Mensagens curtas, diretas e padronizadas.

### Formato

```text
feat: add nearby event search
fix: correct postgis radius query
refactor: simplify event service
```

### Regras

- use prefixo claro
- mantenha a mensagem curta
- descreva a mudança, não a intenção filosófica
- não escreva texto longo de commit

### Prefixos permitidos

- `feat:` nova funcionalidade
- `fix:` correção
- `refactor:` reorganização sem mudar comportamento
- `test:` testes
- `chore:` manutenção
- `docs:` documentação

---

## Regra de ouro

- **Proibido código comentado.** Se não serve, delete.
- **Proibido funções com mais de 30 linhas.** Quebre em funções menores.
- Se uma função cresceu demais, extraia responsabilidade.
- Comentário não substitui clareza de nome ou estrutura.

### Consequência prática

- função longa = dívida técnica
- código comentado = ruído
- duplicação desnecessária = pior para IA corrigir

---

## Regras adicionais

- Pydantic V2 para entrada e saída.
- PostGIS para tudo que for espacial.
- Redis para tarefas assíncronas e pub/sub.
- FastAPI sempre com handlers `async`.
- Service layer para regra de negócio.

---

## Leitura para IA

Se houver dúvida entre duas opções:

1. escolha a mais simples
2. escolha a mais tipada
3. escolha a mais fácil de corrigir
4. escolha a que reduz arquivos tocados no futuro

O objetivo é manter o sistema rápido de evoluir e fácil de substituir.
    return result.scalars().all()
```

---

## 🔌 API & FastAPI

### Router Organization

```python
# app/api/events.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_session

router = APIRouter(
    prefix="/api/events",
    tags=["events"],
)

@router.post(
    "/",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar evento",
)
async def create_event(
    event_data: EventCreate,
    session: AsyncSession = Depends(get_session),
):
    """Descrição completa da operação."""
    ...
```

### Include Routers no Main

```python
# main.py
from app.api import events_router

app.include_router(events_router)
# Resulta em: /api/events
```

### Response Models

**Sempre use schemas Pydantic para respostas:**

```python
# ❌ RUIM - Retorna modelo ORM direto
@router.get("/{event_id}")
async def get_event(event_id: str, session: AsyncSession = Depends(...)):
    event = await session.get(Event, event_id)
    return event  # ❌ Serialização automática pode expor dados sensíveis

# ✅ BOM - Usa schema de resposta
@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str, session: AsyncSession = Depends(...)):
    event = await session.get(Event, event_id)
    return event  # ✅ Serializado pelo schema Pydantic
```

### Error Handling

```python
from fastapi import HTTPException, status

# Para erros esperados, use HTTPException
if not event:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Evento {event_id} não encontrado",
    )

# Para erros não-tratados, deixe a execução falhar
# FastAPI retorna 500 automaticamente
```

### Dependency Injection

```python
from timeit import default_timer as timer

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency para sessão do DB"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

@router.get("/events")
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """O session é injetado automaticamente"""
    ...
```

---

## 🧪 Testes

### Estrutura de Testes

```
tests/
├── conftest.py              # Fixtures compartilhadas
├── test_models.py           # Testes de models
├── test_schemas.py          # Validação de schemas
├── test_api/
│   ├── test_events.py       # API endpoints
│   └── test_matching.py
└── test_services.py         # Business logic
```

### Fixtures Pytest

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.models import Event

@pytest.fixture
async def db_session():
    """Database session para testes"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()

@pytest.fixture
async def sample_event(db_session):
    """Evento de exemplo para testes"""
    event = Event(
        title="Test Event",
        sport="futsal",
        latitude=-23.5505,
        longitude=-46.6333,
        ...
    )
    db_session.add(event)
    await db_session.commit()
    return event
```

### Test Pattern

```python
# tests/test_api/test_events.py
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_create_event(client, db_session):
    """Testa criação de evento"""
    response = client.post(
        "/api/events",
        json={
            "title": "Futsal Test",
            "sport": "futsal",
            "latitude": -23.5505,
            "longitude": -46.6333,
            ...
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Futsal Test"
    assert "id" in data
```

---

## 🔐 Segurança

### Input Validation

**Use Pydantic para validar todos os inputs:**

```python
from pydantic import BaseModel, Field, validator

class EventCreate(BaseModel):
    title: str = Field(
        min_length=3,      # ✅ Valida tamanho mínimo
        max_length=200,    # ✅ Valida tamanho máximo
    )
    latitude: float = Field(
        ge=-90,            # ✅ Geater or equal
        le=90,             # ✅ Less or equal
    )
    skill_level: str = Field(default="intermediate")
    
    @validator("skill_level")
    def validate_skill_level(cls, v):
        """✅ Validação customizada"""
        valid_levels = {"beginner", "intermediate", "advanced"}
        if v.lower() not in valid_levels:
            raise ValueError(f"Skill inválido: {valid_levels}")
        return v.lower()
```

### Rate Limiting (Fase 2)

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/events")
@limiter.limit("10/minute")
async def create_event(...):
    """Máximo 10 criações por minuto"""
    pass
```

### Environment Variables

```python
# ✅ Sensitive data em .env (nunca em código)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str  # Carregado de .env
    secret_key: str    # NUNCA hardcoded
    
    class Config:
        env_file = ".env"
```

---

## ⚡ Performance

### Database Índices

```python
# ✅ Índices essenciais
class Event(SQLModel, table=True):
    id: str = Field(primary_key=True)
    status: str = Field(index=True)  # Frequente filtro
    organizer_id: str = Field(index=True)
    
    # ✅ Índice geoespacial (criado em database.py)
    location: Geometry = Field(sa_column=Column(
        Geometry(...),
        comment="GIST index criado em init_db()"
    ))
```

### Query Optimization

```python
# ❌ N+1 Problem
events = await get_events(session)  # 1 query
for event in events:
    athlete = await session.get(Athlete, event.organizer_id)  # N queries

# ✅ Solução - Join ou eager load
from sqlalchemy.orm import joinedload

result = await session.execute(
    select(Event).options(
        joinedload(Event.organizer)
    )
)
events = result.unique().scalars().all()
```

### Caching (Fase 2)

```python
# Redis para cache de eventos populares
from app.core.redis import redis_client

async def get_popular_events(limit: int = 20):
    cache_key = f"popular_events:{limit}"
    
    # Tenta cache
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from DB
    events = await query_popular_events(limit)
    
    # Store in cache (1 hora)
    await redis_client.setex(
        cache_key,
        3600,
        json.dumps(events),
    )
    
    return events
```

### Async/Await

```python
# ✅ BOM - Async throughout
async def find_events(session: AsyncSession) -> List[Event]:
    result = await session.execute(select(Event))
    return result.scalars().all()

# ❌ RUIM - Sync dentro de async
async def find_events(session: AsyncSession) -> List[Event]:
    # Bloqueia toda a aplicação!
    time.sleep(1)  # ❌ Nunca use sleep em async
    ...
```

---

## 🚀 Checklist para PRs

Antes de fazer commit:

- [ ] Black formatter: `black app/ tests/`
- [ ] Flake8 lint: `flake8 app/ tests/`
- [ ] Type hints: `mypy app/`
- [ ] Testes passam: `pytest`
- [ ] Cobertura >80%: `pytest --cov=app`
- [ ] Sem secrets em código (.env só)
- [ ] Docstrings em funções públicas
- [ ] SQL queries otimizadas

---

**Desenvolvendo com excelência! 🎯**
