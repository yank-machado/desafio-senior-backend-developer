import os
import pytest
import asyncio

# Configurar variáveis de ambiente para testes
os.environ["TESTING"] = "True"
os.environ["DB_HOST"] = "localhost"

@pytest.fixture(scope="session")
def event_loop():
    """
    Cria um loop de eventos para testes assíncronos.
    Esta fixture é usada por pytest-asyncio.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close() 