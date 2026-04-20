@echo off
REM 🐳 Docker Setup Script for Windows/WSL2 - Matching Esportivo

echo.
echo 🚀 Matching Esportivo - Docker Initialization (Windows)
echo =====================================================
echo.

REM 1. Criar diretórios de dados
echo 📁 Criando diretórios de persistência...
if not exist "data\postgres" mkdir data\postgres
if not exist "data\redis" mkdir data\redis
echo ✅ Diretórios criados
echo.

REM 2. Verificar docker e docker-compose
echo 🐳 Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker não encontrado. Instale Docker Desktop.
    pause
    exit /b 1
)
echo ✅ Docker encontrado
echo.

REM 3. Parar containers existentes
echo 🛑 Parando containers existentes...
docker-compose down 2>nul
echo ✅ Containers parados
echo.

REM 4. Pull images
echo 📥 Baixando imagens docker...
docker-compose pull
echo ✅ Imagens baixadas
echo.

REM 5. Iniciar containers
echo 🚀 Iniciando containers...
docker-compose up -d
echo ✅ Containers iniciados
echo.

REM 6. Aguardar serviços
echo ⏳ Aguardando serviços ficarem prontos...
timeout /t 5 /nobreak
echo ✅ Serviços prontos
echo.

REM 7. Status
echo 🎉 Setup completo!
echo.
echo 📊 Status dos containers:
docker-compose ps
echo.
echo 🌐 Acessos:
echo.   PostgreSQL:  localhost:5432
echo.   Redis:       localhost:6379
echo.   PgAdmin:     http://localhost:5050
echo.
echo 🚀 Próximo passo:
echo.   1. python -m venv venv ^&^& venv\Scripts\activate
echo.   2. pip install -r requirements.txt
echo.   3. python main.py
echo.
pause
