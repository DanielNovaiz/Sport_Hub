# ⚡ Quick Reference - Cheat Sheet

## 🚀 Start Project Em 5 Minutos

```bash
# 1. Clone e setup
cd matching-esportivo
cp .env.example .env
python3.11 -m venv venv
source venv/bin/activate

# 2. Instale deps
pip install -r requirements.txt

# 3. Inicie containers
docker-compose up -d

# 4. Verifique saúde
docker-compose ps
docker exec matching_redis redis-cli ping  # PONG ✓

# 5. Rode app
python main.py

# 6. Acesse
# Swagger: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

## 📡 API Quick Test

```bash
# 1. Create Event
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Futsal",
    "sport": "futsal",
    "skill_level": "intermediate",
    "latitude": -23.5505,
    "longitude": -46.6333,
    "address": "São Paulo, SP",
    "scheduled_date": "2024-12-25T18:00:00",
    "max_participants": 12
  }'

# 2. Search Nearby
curl -X POST http://localhost:8000/api/events/search/nearby \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -23.5505,
    "longitude": -46.6333,
    "radius_km": 15,
    "sport": "futsal",
    "limit": 20
  }'

# 3. Get Event
curl http://localhost:8000/api/events/{event_id}

# 4. List Events
curl http://localhost:8000/api/events?skip=0&limit=20
```

---

## 🗂️ File Structure Essentials

```
matching-esportivo/
├── app/models/        # SQLModel (ORM) - Edit aqui para novos models
├── app/schemas/       # Pydantic - Edit para validação input/output
├── app/api/           # FastAPI routers - Add endpoints aqui
├── app/services/      # Business logic - Core algorithms aqui
├── app/core/
│   ├── config.py      # Settings - .env variables
│   └── database.py    # SQLAlchemy engine/session
├── main.py            # Application entry point
├── docker-compose.yml # Containers: PostgreSQL, Redis
├── requirements.txt   # Python dependencies
└── .env              # (Create from .env.example)
```

---

## 🔧 Common Tasks

### Adicionar Novo Endpoint

```python
# 1. Crie schema em app/schemas/

from pydantic import BaseModel

class MyRequest(BaseModel):
    field1: str
    field2: int

class MyResponse(BaseModel):
    id: str
    field1: str
    field2: int

# 2. Crie router em app/api/

from fastapi import APIRouter
from app.schemas import MyRequest, MyResponse

router = APIRouter(prefix="/api/myrouter", tags=["mytag"])

@router.post("/", response_model=MyResponse)
async def my_endpoint(request: MyRequest):
    """Endpoint description."""
    return {"id": "123", **request.dict()}

# 3. Include em main.py

from app.api import myrouter
app.include_router(myrouter.router)
```

### Adicionar Novo Model

```python
# app/models/mymodel.py

from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class MyModel(SQLModel, table=True):
    __tablename__ = "mymodel"
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
    )
    title: str = Field(min_length=3, max_length=200)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Depois inclua em app/models/__init__.py
```

### Adicionar Novo Service

```python
# app/services/myservice.py

from sqlalchemy.ext.asyncio import AsyncSession
from app.models import MyModel

class MyService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def my_method(self) -> MyModel:
        from sqlalchemy import select
        result = await self.session.execute(select(MyModel))
        return result.scalars().first()
```

### Query Geoespacial

```python
from sqlalchemy import select, func
from geoalchemy2.elements import WKTElement

# Criar ponto
location = WKTElement(f"POINT({lng} {lat})", srid=4326)

# Buscar eventos próximos (15km)
distance_degrees = 15 / 111.32  # Converter km para graus

result = await session.execute(
    select(Event).where(
        func.ST_DWithin(
            Event.location,
            func.ST_GeomFromText(f"POINT({lng} {lat})", 4326),
            distance_degrees,
        )
    ).order_by(
        func.ST_Distance(Event.location, ...) * 111.32
    )
)
events = result.scalars().all()
```

---

## 🧪 Testing

```bash
# Rodar testes
pytest

# Com cobertura
pytest --cov=app

# Modo verbose
pytest -v

# Um arquivo específico
pytest tests/test_models.py

# Teste específico
pytest tests/test_models.py::test_event_creation
```

### Estrutura Teste Básico

```python
# tests/test_models.py

import pytest
from app.models import Event
from datetime import datetime

@pytest.fixture
async def sample_event():
    """Fixture - cria evento mock"""
    return Event(
        title="Test Event",
        sport="futsal",
        skill_level="intermediate",
        latitude=-23.5505,
        longitude=-46.6333,
        address="Test Address",
        scheduled_date=datetime.now(),
    )

@pytest.mark.asyncio
async def test_event_creation(sample_event):
    """Testa criação de evento"""
    assert sample_event.title == "Test Event"
    assert sample_event.sport == "futsal"
```

---

## 🔍 Database Inspection

```bash
# Conectar ao PostgreSQL
docker exec -it matching_postgres psql -U postgres -d matching_db

# Dentro do psql:
\dt                           # List tables
SELECT * FROM event LIMIT 5;  # View events
\d event                      # Schema da tabela
SELECT postgis_version();     # Check PostGIS
\q                           # Sair

# Via Redis
docker exec -it matching_redis redis-cli
GET key_name
KEYS *
DEL key_name
QUIT
```

---

## 📋 Code Quality

```bash
# Black format
black app/

# Flake8 lint
flake8 app/ tests/

# Type checking
mypy app/

# Sort imports
isort app/

# All at once
black app/ && isort app/ && flake8 app/ && mypy app/
```

---

## 🐛 Troubleshooting

| Erro | Solução |
|------|---------|
| `ConnectionRefusedError` | `docker-compose ps` e `docker-compose up -d` |
| `ModuleNotFoundError: geoalchemy2` | `pip install --force-reinstall -r requirements.txt` |
| `PostGIS not found` | No psql: `CREATE EXTENSION postgis;` |
| `UNIQUE constraint failed` | Email/username duplicado - use outro |
| `Event location is NULL` | Passe `location` como WKTElement |
| `ST_DWithin: Invalid geometry` | Certifique srid=4326, formato POINT(lng lat) |
| `Port 5432 already in use` | `docker-compose down` e depois `up` |

---

## 🔐 Security Checklist

- [ ] `.env` não está em git (check `.gitignore`)
- [ ] Senhas diferentes em dev/prod
- [ ] Input validation com Pydantic
- [ ] SQL injection impossível (use ORM)
- [ ] CORS configurado (Fase 2)
- [ ] Rate limiting (Fase 2)
- [ ] JWT tokens (Fase 2)
- [ ] HTTPS em produção (Fase 3)

---

## 📊 Performance Tips

1. **Sempre use índices** para campos filtrados:
   ```python
   status: str = Field(index=True)
   ```

2. **Use GIST para geoespacial**:
   ```sql
   CREATE INDEX idx_event_location ON event USING GIST(location);
   ```

3. **Evite N+1 queries**:
   ```python
   # ❌ RUIM
   events = await get_all_events()  # 1 query
   for e in events:
       e.athlete = await get_athlete(e.organizer_id)  # N queries
   
   # ✅ BOM
   result = await session.execute(
       select(Event).options(joinedload(Event.organizer))
   )
   events = result.unique().scalars().all()
   ```

4. **Cache com Redis** (Fase 2):
   ```python
   cached = await redis_client.get(f"events:{lat}:{lng}")
   if cached:
       return json.loads(cached)
   ```

---

## 📚 Useful Links

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostGIS Manual](https://postgis.net/docs/)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## 🎯 Roadmap Rápido

| Fase | Objetivo | Timeline |
|------|----------|----------|
| 1 ✅ | Docker + Models + API | Pronto |
| 2 🚧 | Matching + Notificações + Auth | Próximo |
| 3 📱 | Frontend Web/Mobile | Pós-fase 2 |
| 4 🚀 | Produção | Q3 2024 |

---

**Desenvolvendo com eficiência! 🚀**
