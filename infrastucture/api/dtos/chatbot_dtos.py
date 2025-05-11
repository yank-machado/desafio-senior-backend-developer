from pydantic import BaseModel


class ChatbotQuery(BaseModel):
    query: str


class ChatbotResponse(BaseModel):
    response: str