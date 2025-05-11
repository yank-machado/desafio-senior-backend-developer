from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from uuid import uuid4
from enum import Enum, auto
from typing import List
import logging


class DocumentType(str, Enum):
    """
    Enumeração de tipos de documentos suportados.
    """
    ID = "ID"  # ID (RG)
    CPF = "CPF"  # CPF
    PASSPORT = "PASSPORT"  # Passaporte
    DRIVING_LICENSE = "DRIVING_LICENSE"  # Carteira de motorista
    OUTRO = "OUTRO"  # Outro tipo de documento
    
    @classmethod
    def _missing_(cls, value: Any) -> 'DocumentType':
        """
        Método especial chamado quando um valor não é encontrado.
        Permite processamento mais flexível dos valores.
        """
        if isinstance(value, str):
            # Normalização avançada
            normalized = value.upper().strip().replace(' ', '_').replace('-', '_')
            
            # Mapeamentos específicos para casos comuns
            mappings = {
                # Variações de RG
                'RG': 'ID', 'IDENTIDADE': 'ID', 'CARTEIRA_DE_IDENTIDADE': 'ID', 'ID': 'ID',
                # Variações de CPF
                'CPF': 'CPF', 'CADASTRO_DE_PESSOA_FISICA': 'CPF',  
                # Variações de CNH
                'CNH': 'DRIVING_LICENSE', 'CARTEIRA_NACIONAL_DE_HABILITACAO': 'DRIVING_LICENSE', 'DRIVING_LICENSE': 'DRIVING_LICENSE',
                # Variações de Passaporte
                'PASSAPORTE': 'PASSPORT', 'PASSPORT': 'PASSPORT',
                # Outros documentos
                'OUTRO': 'OUTRO', 'OTHER': 'OUTRO'
            }
            
            # Verificar se o valor normalizado está nos mapeamentos
            if normalized in mappings:
                return cls(mappings[normalized])
        
        # Default para OUTRO em caso de falha
        logger.warning(f"Tipo de documento não reconhecido: '{value}'. Usando OUTRO.")
        return cls.OUTRO


@dataclass
class Document:
    user_id: UUID
    document_type: DocumentType
    file_path: str
    name: str
    id: UUID = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        
        # Garantir que document_type seja sempre um enum DocumentType válido
        if not isinstance(self.document_type, DocumentType):
            self.document_type = DocumentType(self.document_type)


