# Desafio Técnico: Carteira Digital API

[![CI](https://github.com/seu-usuario/carteira_digital/actions/workflows/ci.yml/badge.svg)](https://github.com/seu-usuario/carteira_digital/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/seu-usuario/carteira_digital/branch/main/graph/badge.svg)](https://codecov.io/gh/seu-usuario/carteira_digital)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

##  Visão Geral do Projeto

Este projeto é uma implementação de uma API para gerenciamento de carteira digital com documentos e transporte público, desenvolvido como demonstração de proficiência técnica em arquitetura de software e engenharia de back-end. A solução foi construída com foco em Clean Architecture e princípios SOLID.

##  Decisões Arquiteturais

### Arquitetura em Camadas 

O projeto foi estruturado seguindo os princípios da Clean Architecture, com uma clara separação entre:

- **Core**: Contém a lógica de negócio pura e entidades do domínio
  - `entities`: Modelos de domínio independentes de frameworks
  - `use_cases`: Implementação dos casos de uso da aplicação
  - `exceptions`: Definição de exceções de domínio
  - `interfaces`: Contratos que definem comportamentos

- **Infrastructure**: Implementações técnicas e adaptadores
  - `api`: Controllers, DTOs e rotas da API
  - `database`: Configuração e modelos de banco de dados
  - `repositories`: Implementações concretas dos repositórios
  - `security`: Implementações de autenticação e autorização

- **Utils**: Scripts e ferramentas de suporte
  - Utilitários para inicialização do ambiente
  - Ferramentas para gerenciamento de serviços
  - Funções auxiliares comuns

Esta abordagem proporciona:
- Independência de frameworks (regras de negócio não dependem de detalhes técnicos)
- Testabilidade elevada
- Flexibilidade para mudanças tecnológicas
- Manutenibilidade a longo prazo

### Design Patterns Aplicados

- **Dependency Injection**: Utilizado para inverter o controle de dependências
- **Repository Pattern**: Abstraindo o acesso a dados
- **Factory Pattern**: Para criação de objetos complexos
- **Adapter Pattern**: Na integração com serviços externos (OAuth)
- **Strategy Pattern**: Na implementação de diferentes métodos de autenticação

##  Escolhas Tecnológicas e Justificativas

### FastAPI

Optei pelo FastAPI como framework web pelos seguintes motivos:
- **Performance**: Construído sobre Starlette e Pydantic, oferece desempenho excepcional
- **Documentação Automática**: Geração de Swagger/OpenAPI sem configuração adicional
- **Tipagem**: Suporte nativo a type hints do Python, melhorando a segurança do código
- **Validação Automática**: Validação de dados de entrada via Pydantic
- **Assincronicidade**: Suporte nativo a operações assíncronas, essencial para escala

### SQLAlchemy + Alembic

A combinação do SQLAlchemy como ORM e Alembic para migrations proporciona:
- **Abstração de Banco de Dados**: Possibilidade de trocar o SGBD com mínimo impacto
- **Segurança**: Prevenção contra SQL Injection
- **Versionamento de Banco**: Controle preciso da evolução do schema
- **Query Builder**: Construção de queries complexas com tipagem segura

### PostgreSQL

A escolha do PostgreSQL como banco de dados foi baseada em:
- **Confiabilidade**: Sistema maduro e estável para dados críticos
- **Suporte a JSON**: Armazenamento flexível quando necessário
- **Recursos Avançados**: Indexação de texto completo, operações geoespaciais
- **Integridade Transacional**: Garantias ACID completas

### JWT + OAuth2 + PyOTP (Autenticação)

A estratégia de autenticação multi-camada foi implementada para:
- **Segurança em Profundidade**: Múltiplas camadas de proteção
- **Experiência do Usuário**: Flexibilidade nas opções de login
- **Integração com Ecossistemas**: Login social para reduzir fricção
- **Proteção Adicional**: MFA como camada extra de segurança

### Docker e Docker Compose

A containerização da aplicação proporciona:
- **Consistência de Ambiente**: Eliminação do problema inconcistencia de ambiente em outras maaquinas
- **Isolamento**: Dependências encapsuladas e gerenciadas
- **Escalabilidade**: Facilidade para escalar horizontalmente
- **DevOps Simplificado**: Integração facilitada com pipelines CI/CD

##  Funcionalidades Implementadas

O sistema implementa os seguintes casos de uso:

### Gestão de Identidade e Acesso
- **Registro e Autenticação**: Sistema completo com múltiplos fatores
- **Login Social**: Integração OAuth2 com Google e Facebook
- **Autorização Baseada em Roles**: Controle granular de permissões

### Gestão de Documentos Digitais
- **Armazenamento Seguro**: Upload e download de documentos com verificação de permissões
- **Categorização**: Organização lógica dos documentos
- **Validação**: Verificação de integridade e autenticidade

### Sistema de Transporte Público
- **Gestão de Saldo**: Consulta e recarga do passe de transporte
- **Simulação de Uso**: Funcionalidade para debitar passagens
- **Histórico de Transações**: Registro completo de operações

### Facilidades para o Usuário
- **Chatbot Integrado**: Sistema de perguntas e respostas para suporte
- **Health Check**: Monitoramento de saúde da aplicação

##  Testes e Qualidade

A qualidade do código é garantida através de:
- **TDD**: Desenvolvimento orientado a testes (unitários, integração)
- **Cobertura de Testes**: Mínimo de 90% de cobertura
- **CI/CD**: Pipeline automatizado via GitHub Actions
- **Linting**: Garantia de conformidade com padrões de código

##  CI/CD e DevOps

A infraestrutura como código implementada visa:
- **Integração Contínua**: Testes automáticos em cada commit
- **Deployment Automatizado**: Configuração para diferentes ambientes
- **Monitoramento**: Endpoints de health check para observabilidade
- **Configuração Externa**: Variáveis de ambiente para diferentes contextos

##  Considerações sobre Escalabilidade

O projeto foi desenhado considerando:
- **Escalabilidade Horizontal**: Serviços stateless prontos para balanceamento
- **Cache Estratégico**: Pontos de cache para otimizar performance
- **Banco de Dados**: Modelagem eficiente e índices otimizados
- **Arquitetura**: Preparada para eventual migração para microserviços

##  Requisitos para Execução

### Ambiente de Desenvolvimento
- Python 3.8+
- PostgreSQL
- Ou Docker/Docker Compose para ambiente isolado

### Configuração e Execução

#### Com Docker
```bash
docker-compose up -d
```

#### Sem Docker
```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Aplicar migrations
alembic upgrade head

# Iniciar servidor de desenvolvimento
python start_dev.py
```

##  Documentação da API

A documentação completa da API está disponível em:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

##  Principais Rotas e Utilização

### Autenticação

#### Registro de Usuário
```
POST /api/v1/auth/register
{
  "email": "usuario@exemplo.com",
  "password": "senha123",
  "full_name": "Nome Completo"
}
```
Cria um novo usuário no sistema.

#### Login Padrão
```
POST /api/v1/auth/login
{
  "email": "usuario@exemplo.com",
  "password": "senha123"
}
```
Retorna um token JWT para autenticação nas demais rotas.

#### Configuração de MFA
```
POST /api/v1/auth/mfa/setup
```
Inicia o processo de configuração da autenticação de múltiplos fatores.

#### Login Social

- **Google**: `GET /api/v1/oauth/google/login`
- **Facebook**: `GET /api/v1/oauth/facebook/login`

Rota para interface de Login social

-`http://localhost:8000/static/login_exemplo.html`

### Documentos Digitais

#### Upload de Documento
```
POST /api/v1/documents/upload
{
  "document_type": "rg",
  "description": "RG digital"
}
```
O arquivo deve ser enviado como um form-data com a chave `file`.

#### Listagem de Documentos
```
GET /api/v1/documents
```
Retorna a lista de documentos do usuário autenticado.

#### Download de Documento
```
GET /api/v1/documents/{document_id}/download
```
Faz o download do documento especificado.

### Transporte Público

#### Consulta de Saldo
```
GET /api/v1/transport/card/balance
```
Retorna o saldo atual do cartão de transporte do usuário.

#### Recarga de Cartão
```
POST /api/v1/transport/card/recharge
{
  "amount": 50.00
}
```
Adiciona créditos ao cartão de transporte.

#### Simulação de Uso
```
POST /api/v1/transport/card/use
{
  "transport_type": "bus",
  "amount": 4.50
}
```
Simula o uso do cartão em um transporte, debitando o valor da passagem.

#### Histórico de Transações
```
GET /api/v1/transport/card/transactions
```
Retorna o histórico de transações do cartão de transporte.

### Chatbot

O chatbot da Carteira Digital é capaz de responder perguntas sobre os seguintes tópicos:

#### Perguntas Disponíveis
```
POST /api/v1/chatbot/query
{
  "query": "Como consulto meu saldo?"
}
```

O chatbot pode responder perguntas como:
- "Como faço para consultar meu saldo?"
- "Como carregar meu cartão de transporte?"
- "Como faço upload de documentos?"
- "Como ativar autenticação de dois fatores?"
- "O que fazer se perder meu cartão?"
- "Quais documentos posso armazenar?"
- "Como funciona o pagamento de passagens?"
- "Existe um limite de recarga no cartão?"
- "Como atualizar meus dados pessoais?"
- "O sistema é seguro?"

Todas as respostas são pré-definidas e focadas em auxiliar o usuário na utilização da plataforma.

### Verificação de Saúde do Sistema
```
GET /api/v1/health
```
Retorna informações sobre o estado atual do sistema, útil para monitoramento.

##  Qualidade de Código

A qualidade do código é garantida através de várias ferramentas e práticas:

- **Formatação**: Black e isort para formato consistente
- **Linting**: Flake8 para análise estática
- **Verificação de tipos**: Mypy para tipagem estática
- **Pre-commit hooks**: Validações automáticas antes de cada commit
- **CI/CD**: Testes e verificações automatizadas via GitHub Actions 

##  Desenvolvimento

### Comandos Úteis

Utilizamos um Makefile para facilitar tarefas comuns:

```bash
make help           # Lista todos os comandos disponíveis
make dev-install    # Instala dependências de desenvolvimento
make lint           # Verifica qualidade do código
make format         # Formata o código automaticamente
make test           # Executa testes
make coverage       # Gera relatório de cobertura de código
make dev            # Inicia ambiente de desenvolvimento
```

### Contribuição

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para obter diretrizes detalhadas sobre como contribuir com este projeto.

### Histórico de Mudanças

Veja [CHANGELOG.md](CHANGELOG.md) para um registro de todas as mudanças notáveis.
