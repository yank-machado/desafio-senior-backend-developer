# Testes da Carteira Digital API

Este diretório contém os testes automatizados da API de Carteira Digital, seguindo os princípios de Clean Architecture.

## Estrutura de Testes

Os testes estão organizados da seguinte forma:

- **Unit**: Testes unitários que verificam o funcionamento individual de componentes isolados
  - `test_user_use_cases.py`: Testes dos casos de uso de usuário (register, login)
  - `test_auth_router.py`: Testes dos endpoints da API relacionados à autenticação

- **Integration**: Testes de integração que verificam a interação entre múltiplos componentes do sistema
  - `test_auth_api.py`: Testes de integração para as rotas de autenticação
  - `test_db_integration.py`: Testes de integração com o banco de dados
  - `test_api.py`: Testes de integração gerais da API
  - `test_health.py`: Testes das rotas de health check

## Executando os Testes

### Preparação do Ambiente

Antes de executar os testes, certifique-se de que:
1. O ambiente virtual está ativado
2. As dependências estão instaladas (`pip install -r requirements.txt`)
3. A variável de ambiente PYTHONPATH está configurada para a raiz do projeto

```bash
# No Linux/macOS
export PYTHONPATH=$(pwd)

# No Windows (PowerShell)
$env:PYTHONPATH = Get-Location

# No Windows (CMD)
set PYTHONPATH=%cd%
```

### Testes Unitários

Estes testes verificam o comportamento de componentes isolados e não precisam de recursos externos como banco de dados.

```bash
pytest tests/unit -v
```

### Testes de Integração

Estes testes verificam a interação entre componentes e podem precisar de recursos externos como banco de dados.

```bash
# Se você estiver usando Docker para o banco de dados
docker-compose up -d db

# Executar testes de integração
pytest tests/integration -v
```

### Testes Específicos

Para executar um teste específico:

```bash
# Por nome do arquivo
pytest tests/unit/test_user_use_cases.py -v

# Por nome da classe
pytest tests/unit/test_user_use_cases.py::TestRegisterUserUseCase -v

# Por nome do método de teste
pytest tests/unit/test_user_use_cases.py::TestRegisterUserUseCase::test_register_new_user_success -v
```

### Todos os Testes

```bash
pytest -v
```

## Convenções de Testes

1. **Nomenclatura**:
   - Arquivos: `test_*.py`
   - Classes: `Test*`
   - Métodos: `test_*`

2. **Organização**:
   - Estrutura AAA: Arrange (preparar), Act (agir), Assert (verificar)
   - Fixtures para configuração compartilhada
   - Mocks para isolar dependências externas

3. **Fixtures**:
   - Parâmetros compartilhados entre testes
   - Configuração de dependências
   - Preparação e limpeza de recursos

4. **Asserções**:
   - Verificações explícitas para cada comportamento esperado
   - Mensagens de erro descritivas
   - Teste de casos de sucesso e falha

## Dicas para Novos Testes

1. Para adicionar novos testes unitários, crie um arquivo `test_*.py` na pasta `tests/unit/`
2. Para adicionar novos testes de integração, crie um arquivo `test_*.py` na pasta `tests/integration/`
3. Use fixtures existentes ou crie novas conforme necessário
4. Mantenha os testes independentes e idempotentes (podem ser executados várias vezes sem efeitos colaterais)

## Estratégia de Testes

1. **Testes Unitários**: Focados em testar a lógica de negócio isoladamente (casos de uso)
   - Usam mocks para isolar dependências
   - Verificam comportamentos específicos

2. **Testes de Integração**: Focados em testar a interação entre componentes
   - Verificam a integração com o banco de dados
   - Testam o fluxo completo de requisições HTTP

## Convenções e Boas Práticas

1. Seguir o padrão AAA (Arrange, Act, Assert)
2. Utilizar fixtures do pytest para configuração
3. Utilizar o marcador `@pytest.mark.asyncio` para testes assíncronos
4. Nomear testes de forma descritiva (`test_should_do_something_when_condition`)
5. Criar mocks para isolar dependências externas nos testes unitários 