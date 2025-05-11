from typing import Dict

class ChatbotQueryUseCase:
    def __init__(self, responses: Dict[str, str]):
        self.responses = responses
    
    def execute(self, query: str) -> str:
        normalized_query = query.lower().strip()
        
        for key, response in self.responses.items():
            if any(keyword in normalized_query for keyword in key.split("|")):
                return response
        
        return "Desculpe, não entendi sua pergunta. Poderia reformular ou escolher outra opção?"