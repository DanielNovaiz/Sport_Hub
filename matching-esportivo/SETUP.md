# 🚀 Guia de Setup e Testes - Projeto Matching Esportivo

## 1️⃣ Setup Inicial Completo

### No WSL2 (Ubuntu)

```bash
# 1. Navegue até a pasta do projeto
cd ~/projects/matching-esportivo

# 2. Copie arquivos de configuração
cp .env.example .env

# 3. Criar virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 4. Instale dependências
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 5. Inicie Docker containers
docker-compose up -d

# 6. Verifique status
docker-compose ps
```

### Verificação de Saúde

```bash
# PostgreSQL
docker-compose logs postgres | grep -i "ready"

# Redis
docker exec matching_redis redis-cli ping
# Output esperado: PONG

# PgAdmin (opcional)
docker-compose --profile dev up -d pgadmin
# Acesse: http://localhost:5050
```

## 2️⃣ Iniciar a Aplicação

```bash
# Terminal 1: Aplicação FastAPI
cd matching-esportivo
source venv/bin/activate
python main.py

# Output esperado:
# 🚀 Iniciando Matching Esportivo
# ✅ Banco de dados inicializado
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

Acesse:
- 📚 **Swagger UI**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc
- ❤️ **Health**: http://localhost:8000/health

## 3️⃣ Testes com cURL

### Health Check

```bash
curl -X GET "http://localhost:8000/health"
# {"status":"ok"}
```

### Criar Evento

```bash
curl -X POST "http://localhost:8000/api/events" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Futsal no Parque Ibirapuera",
    "description": "Partida amistosa de futsal, todos bem-vindos!",
    "sport": "futsal",
    "skill_level": "intermediate",
    "latitude": -23.5505,
    "longitude": -46.6333,
    "address": "Parque Ibirapuera, São Paulo, SP",
    "scheduled_date": "2024-12-25T18:00:00",
    "duration_minutes": 90,
    "max_participants": 12
  }'
```

**Response esperada:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Futsal no Parque Ibirapuera",
  "sport": "futsal",
  "skill_level": "intermediate",
  "latitude": -23.5505,
  "longitude": -46.6333,
  "address": "Parque Ibirapuera, São Paulo, SP",
  "scheduled_date": "2024-12-25T18:00:00",
  "max_participants": 12,
  "current_participants": 1,
  "organizer_id": "temp_user_id",
  "status": "open",
  "created_at": "2024-04-13T10:30:45.123456",
  "updated_at": "2024-04-13T10:30:45.123456"
}
```

### Buscar Eventos Próximos

```bash
curl -X POST "http://localhost:8000/api/events/search/nearby" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -23.5505,
    "longitude": -46.6333,
    "radius_km": 15.0,
    "sport": "futsal",
    "skill_level": "intermediate",
    "limit": 20
  }'
```

**Response esperada:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Futsal no Parque Ibirapuera",
    "sport": "futsal",
    "latitude": -23.5505,
    "longitude": -46.6333,
    "distance_km": 2.3,
    "status": "open",
    ...
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Futsal Vila Madalena",
    "sport": "futsal",
    "latitude": -23.5510,
    "longitude": -46.6400,
    "distance_km": 5.1,
    "status": "open",
    ...
  }
]
```

### Obter Evento Específico

```bash
curl -X GET "http://localhost:8000/api/events/550e8400-e29b-41d4-a716-446655440000"
```

### Listar Todos os Eventos

```bash
curl -X GET "http://localhost:8000/api/events?skip=0&limit=20"
```

## 4️⃣ Testes com Python (httpx)

Crie arquivo `test_api.py`:

```python
import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_create_and_search():
    async with httpx.AsyncClient() as client:
        # 1. Criar evento
        response = await client.post(
            f"{BASE_URL}/api/events",
            json={
                "title": "Vôlei de Praia",
                "description": "Vôlei de praia na Praia Grande",
                "sport": "vôlei",
                "skill_level": "beginner",
                "latitude": -24.0043,
                "longitude": -46.4025,
                "address": "Praia Grande, SP",
                "scheduled_date": "2024-12-26T14:00:00",
                "duration_minutes": 120,
                "max_participants": 8,
            }
        )
        print(f"✅ Evento criado: {response.status_code}")
        event = response.json()
        print(f"   ID: {event['id']}")
        
        # 2. Buscar eventos próximos
        response = await client.post(
            f"{BASE_URL}/api/events/search/nearby",
            json={
                "latitude": -24.0043,
                "longitude": -46.4025,
                "radius_km": 50.0,
                "skill_level": "beginner",
                "limit": 10,
            }
        )
        print(f"✅ Busca realizada: {response.status_code}")
        events = response.json()
        print(f"   Encontrados: {len(events)} eventos")

# Executar
asyncio.run(test_create_and_search())
```

```bash
python test_api.py
```

## 5️⃣ Inspecionar Database

### Via Docker SQL

```bash
# Conectar ao PostgreSQL
docker exec -it matching_postgres psql -U postgres -d matching_db

# Dentro do psql:
\dt                          # Listar tabelas
SELECT * FROM event LIMIT 5; # Ver eventos
SELECT postgis_version();    # Verificar PostGIS
\q                           # Sair
```

### Via PgAdmin

1. Acesse http://localhost:5050
2. Login: admin@admin.com / admin
3. Adicione servidor:
   - **Host**: postgres
   - **Port**: 5432
   - **Database**: matching_db
   - **User**: postgres
   - **Password**: postgres_dev_password

## 6️⃣ Troubleshooting

### Erro: "ConnectionRefusedError: Connection refused"

```bash
# Verificar se containers estão rodando
docker-compose ps

# Se não estão, iniciar:
docker-compose up -d

# Logs do postgres
docker-compose logs postgres
```

### Erro: "ModuleNotFoundError: No module named 'geoalchemy2'"

```bash
# Reinstalar dependências
pip install --force-reinstall geoalchemy2
pip install -r requirements.txt
```

### Erro: "PostGIS not found"

```bash
# No psql:
CREATE EXTENSION postgis;
SELECT postgis_version();
```

### Limpar e Recomeçar

```bash
# Parar containers
docker-compose down

# Remover volumes (cuidado - deleta dados!)
docker volume rm matching-esportivo_postgres_data

# Recomeçar
docker-compose up -d
python main.py
```

## 7️⃣ Monitoramento

### Logs em Tempo Real

```bash
# Aplicação Python
tail -f main.log

# PostgreSQL
docker-compose logs -f postgres

# Redis
docker-compose logs -f redis

# Todos
docker-compose logs -f
```

### Performance

```bash
# Top de queries lentas
docker exec -it matching_postgres psql -U postgres -d matching_db -c \
  "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Uso de índices
docker exec -it matching_postgres psql -U postgres -d matching_db -c \
  "SELECT schemaname, tablename, indexname FROM pg_indexes WHERE tablename='event';"
```

---

**💡 Próximas Fases:**
- Fase 2: Testes automatizados com pytest
- Fase 3: CI/CD com GitHub Actions
- Fase 4: Deploy em AWS/Heroku
