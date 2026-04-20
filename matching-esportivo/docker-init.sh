#!/bin/bash

# 🐳 Docker Setup Script for WSL2 - Matching Esportivo
# Inicializa volumes e containers de forma segura

set -e

echo "🚀 Matching Esportivo - Docker Initialization"
echo "============================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Criar diretórios de dados
echo -e "${YELLOW}📁 Criando diretórios de persistência para WSL2...${NC}"
mkdir -p data/postgres
mkdir -p data/redis
chmod 755 data/postgres data/redis
echo -e "${GREEN}✅ Diretórios criados${NC}"

# 2. Verificar Docker
echo -e "${YELLOW}🐳 Verificando Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não encontrado. Instale Docker Desktop com WSL2 integration.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker encontrado: $(docker --version)${NC}"

# 3. Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose não encontrado.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose encontrado: $(docker-compose --version)${NC}"

# 4. Parar containers existentes (se houver)
echo -e "${YELLOW}🛑 Parando containers existentes...${NC}"
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✅ Containers parados${NC}"

# 5. Pull images
echo -e "${YELLOW}📥 Baixando imagens docker...${NC}"
docker-compose pull
echo -e "${GREEN}✅ Imagens baixadas${NC}"

# 6. Iniciar containers
echo -e "${YELLOW}🚀 Iniciando containers...${NC}"
docker-compose up -d
echo -e "${GREEN}✅ Containers iniciados${NC}"

# 7. Aguardar PostgreSQL estar pronto
echo -e "${YELLOW}⏳ Aguardando PostgreSQL estar pronto...${NC}"
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
        echo -e "${GREEN}✅ PostgreSQL pronto${NC}"
        break
    fi
    echo "   Tentativa $i/30..."
    sleep 2
done

# 8. Verificar PostGIS
echo -e "${YELLOW}🌍 Verificando PostGIS...${NC}"
POSTGIS_VERSION=$(docker-compose exec -T postgres psql -U postgres -d matching_db -c "SELECT postgis_version();" 2>/dev/null || echo "Not installed")
echo -e "${GREEN}✅ PostGIS: $POSTGIS_VERSION${NC}"

# 9. Aguardar Redis estar pronto
echo -e "${YELLOW}⏳ Aguardando Redis estar pronto...${NC}"
for i in {1..10}; do
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis pronto${NC}"
        break
    fi
    echo "   Tentativa $i/10..."
    sleep 1
done

# 10. Status final
echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}🎉 Setup completo!${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo "📊 Status dos containers:"
docker-compose ps
echo ""
echo "🌐 Acessos:"
echo "  PostgreSQL:  localhost:5432"
echo "  Redis:       localhost:6379"
echo "  PgAdmin:     http://localhost:5050 (admin@admin.com / admin)"
echo ""
echo "🚀 Para iniciar a aplicação FastAPI:"
echo "  python main.py"
echo ""
echo "📋 Para ver logs:"
echo "  docker-compose logs -f postgres"
echo "  docker-compose logs -f redis"
echo ""
echo "🛑 Para parar containers:"
echo "  docker-compose down"
echo ""
