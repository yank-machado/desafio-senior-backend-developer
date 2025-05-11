import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import os
from dotenv import load_dotenv

from main import app

# Carregar variáveis de ambiente
load_dotenv()

# Cliente de teste
client = TestClient(app)

@pytest.mark.asyncio
async def test_root_endpoint():
    """Testa a rota raiz da API."""
    base_url = "http://localhost:8000"
    async with AsyncClient(base_url=base_url) as ac:
        response = await ac.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "redoc" in data

@pytest.mark.asyncio
async def test_health_endpoint():
    """Testa a rota de health check da API."""
    base_url = "http://localhost:8000"
    async with AsyncClient(base_url=base_url) as ac:
        response = await ac.get("/api/v1/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "online"
        assert "database" in data
        assert data["database"] == "connected"

@pytest.mark.asyncio
async def test_health_db_endpoint():
    """Testa a rota de verificação de saúde do banco de dados."""
    base_url = "http://localhost:8000"
    async with AsyncClient(base_url=base_url) as ac:
        response = await ac.get("/api/v1/health/db")
        
        # O status pode ser 200 (conectado) ou 503 (erro)
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "ok"
            assert data["database"] == "connected"
        else:
            # Se o banco não estiver disponível, deve retornar 503
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "error"
            assert data["database"] == "error"

@pytest.mark.asyncio
async def test_routes_endpoint():
    """Testa a rota que lista todas as rotas disponíveis na API."""
    base_url = "http://localhost:8000"
    async with AsyncClient(base_url=base_url) as ac:
        response = await ac.get("/routes")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verificar se cada item na lista tem os campos esperados
        for route in data:
            assert "path" in route
            assert "name" in route
            assert "methods" in route
        
        # Verificar se as rotas principais estão listadas
        route_paths = [route["path"] for route in data]
        assert "/" in route_paths
        assert "/routes" in route_paths
        
        # Verificar se as rotas de autenticação estão presentes
        auth_routes = [path for path in route_paths if "auth" in path]
        assert len(auth_routes) >= 2  # Deve ter pelo menos register e login

        # Verificar se as rotas de health check estão presentes
        health_routes = [path for path in route_paths if "health" in path]
        assert len(health_routes) >= 2  # Deve ter pelo menos / e /db 