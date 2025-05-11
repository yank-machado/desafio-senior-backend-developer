from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from core.entities.document import DocumentType


class DocumentCreate(BaseModel):
    document_type: DocumentType
    name: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_type": "RG",
                "name": "RG Principal"
            }
        }


class DocumentResponse(BaseModel):
    id: UUID
    user_id: UUID
    document_type: str = Field(..., description="Tipo do documento (ex: RG, CPF, CNH, etc.)")
    file_path: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
        @staticmethod
        def schema_extra(schema, model):
            # Ajustar o schema para usar o valor do enum no exemplo
            if "properties" in schema and "document_type" in schema["properties"]:
                schema["properties"]["document_type"]["example"] = "RG"
                
    def __init__(self, **data):
        # Certificar que document_type sempre seja serializado como string
        if "document_type" in data and hasattr(data["document_type"], "value"):
            data["document_type"] = data["document_type"].value
        super().__init__(**data)