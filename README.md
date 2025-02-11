# Desafio Técnico – Desenvolvedor(a) Back-end Sênior

Bem-vindo(a) ao desafio técnico para a vaga de Pessoa Desenvolvedora Back-end Sênior!

Nosso objetivo com este desafio é avaliar suas habilidades técnicas em FastAPI, bancos de dados, arquitetura de APIs e boas práticas de desenvolvimento back-end.

## 📌 Contexto

A Prefeitura do Rio de Janeiro quer oferecer aos cidadãos uma **API de Carteira Digital**, onde os usuários poderão armazenar e gerenciar documentos digitais, consultar e carregar créditos do transporte público e acessar serviços municipais via chatbot.

Seu desafio será desenvolver uma API para essa carteira digital, simulando as interações do usuário com documentos e transporte público.

## ✨ Requisitos do Desafio

### 🔹 Funcionalidades Esperadas

- Autenticação e Gerenciamento de Usuários
    - Cadastro e login de usuários (simples, com e-mail/senha).
    - Uso de tokens JWT para autenticação.
    - [Diferencial] Integração com OAuth2 (Google, Facebook, etc).
    - [Diferencial] Multi-factor authentication (MFA).

- Gestão de Documentos
    - Endpoint para armazenar e listar documentos digitais (exemplo: identidade, CPF, comprovante de vacinação).

- Gestão de Transporte Público
    - Endpoint para consultar saldo do passe de transporte público (mockado).
    - Endpoint para simular recarga do passe.

- Integração com Chatbot (Simples)
    - Endpoint que recebe uma pergunta do usuário e retorna uma resposta pré-definida (simulação de um chatbot).

### 🔹 Requisitos Técnicos

- FastAPI como framework principal.
- Banco de Dados Relacional (PostgreSQL ou MySQL, usando ORM como SQLAlchemy ou Tortoise-ORM).
- Ferramenta de migrations (Alembic, Aerich, etc).
- Testes automatizados para pelo menos uma funcionalidade crítica.
- Documentação da API (usando OpenAPI gerado pelo FastAPI e README explicativo).
- Endpoint de verificação de saúde da API (por exemplo, `/health`).
- Configuração de CI/CD (um workflow simples no GitHub Actions ou equivalente para rodar os testes automaticamente).
- Dockerfile e/ou docker-compose para rodar o projeto facilmente.

## 🏗️ Como Submeter o Desafio

1. Faça um fork ou clone este repositório.
2. Implemente a solução seguindo os requisitos descritos.
3. Inclua um pequeno documento (ou atualize este README) explicando suas decisões técnicas, estrutura do código e instruções para rodar o projeto.
4. Envie o link do repositório para nós!

## 📖 O que será avaliado?

- Código limpo e bem estruturado.
- Boas práticas com FastAPI e Python.
- Modelagem eficiente do banco de dados.
- Testes automatizados.
- Configuração de CI/CD e Docker.
- Documentação clara da API e do projeto.

## ❓ Dúvidas?

Se tiver qualquer dúvida, fique à vontade para perguntar!

Boa sorte! 🚀