from fastapi import APIRouter, Depends

from infrastucture.api.dtos.chatbot_dtos import ChatbotQuery, ChatbotResponse
from core.use_cases.chatbot_use_cases import ChatbotQueryUseCase

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Respostas pré-definidas para o chatbot simples
CHATBOT_RESPONSES = {
    "saldo|balanço|dinheiro": "Para consultar seu saldo, acesse a seção 'Transporte' e clique em 'Consultar Saldo'.",
    "recarga|recarregar|carregar": "Para recarregar seu cartão, acesse a seção 'Transporte' e clique em 'Recarregar'.",
    "documento|documentos|identidade|cpf": "Para gerenciar seus documentos, acesse a seção 'Documentos'.",
    "ajuda|help|socorro": "Como posso ajudar? Você pode perguntar sobre saldo, recarga, documentos ou outras funções da carteira digital.",
    "login|entrar|acessar": "Para fazer login, use seu email e senha cadastrados.",
    "cadastro|registrar|criar conta": "Para se cadastrar, acesse a página inicial e clique em 'Criar Conta'."
}

@router.post("/query", response_model=ChatbotResponse)
async def query_chatbot(query: ChatbotQuery):
    # Caso de uso
    chatbot_use_case = ChatbotQueryUseCase(CHATBOT_RESPONSES)
    response = chatbot_use_case.execute(query.query)
    
    return ChatbotResponse(response=response)