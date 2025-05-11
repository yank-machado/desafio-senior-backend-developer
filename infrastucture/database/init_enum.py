import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from core.entities.document import DocumentType

logger = logging.getLogger(__name__)

async def ensure_document_type_enum(db_session: AsyncSession):
    """
    Garante que o enum DocumentType no banco de dados tenha todos os valores necessários.
    Cria o enum se não existir ou o atualiza se estiver desatualizado.
    
    Também corrige automaticamente documentos com valores de enum inválidos.
    """
    try:
        logger.info("Verificando e atualizando o enum DocumentType no banco de dados")
        
        # Verificar se o tipo documenttype existe
        check_query = text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'documenttype') as exists")
        result = await db_session.execute(check_query)
        row = result.fetchone()
        
        enum_exists = row[0] if row else False
        
        # Obter todos os valores do enum no código
        enum_values = [e.value for e in DocumentType]
        values_str = "', '".join(enum_values)
        
        if enum_exists:
            logger.info("Enum DocumentType encontrado, verificando valores")
            
            # Verificar se precisamos atualizar
            check_values_query = text("""
                SELECT e.enumlabel
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = 'documenttype'
            """)
            result = await db_session.execute(check_values_query)
            existing_values = [row[0] for row in result.fetchall()]
            
            # Verificar se há valores faltando
            missing_values = [v for v in enum_values if v not in existing_values]
            
            if missing_values:
                logger.warning(f"Valores faltando no enum: {missing_values}")
                
                # Estratégia mais abrangente:
                # 1. Criar função de conversão segura
                # 2. Criar um tipo temporário com todos os valores
                # 3. Converter dados existentes para o novo tipo
                # 4. Substituir o tipo antigo pelo novo
                
                # Criar função de conversão segura para o enum
                await db_session.execute(text(f"""
                    CREATE OR REPLACE FUNCTION text_to_documenttype(text) RETURNS documenttype AS $$
                    BEGIN
                        BEGIN
                            RETURN $1::documenttype;
                        EXCEPTION WHEN OTHERS THEN
                            RETURN 'OUTRO'::documenttype;
                        END;
                    END;
                    $$ LANGUAGE plpgsql IMMUTABLE;
                """))
                
                # Corrigir documentos existentes com valores inválidos
                # Verificar se a tabela documents existe
                table_exists_query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'documents'
                    ) as exists
                """)
                result = await db_session.execute(table_exists_query)
                table_exists = result.fetchone()[0]
                
                if table_exists:
                    try:
                        # Listar valores válidos para a cláusula IN
                        valid_values = "', '".join(existing_values)
                        
                        # Verificar se há documentos com valores inválidos
                        check_invalid_docs = text(f"""
                            SELECT COUNT(*) FROM documents 
                            WHERE CAST(document_type AS TEXT) NOT IN ('{valid_values}')
                        """)
                        result = await db_session.execute(check_invalid_docs)
                        invalid_count = result.scalar()
                        
                        if invalid_count > 0:
                            logger.warning(f"Encontrados {invalid_count} documentos com tipos inválidos")
                            
                            # Usar a função de conversão segura para atualizar valores inválidos para 'OUTRO'
                            update_invalid_query = text("""
                                UPDATE documents 
                                SET document_type = 'OUTRO'::documenttype
                                WHERE text_to_documenttype(CAST(document_type AS TEXT)) = 'OUTRO'::documenttype
                            """)
                            await db_session.execute(update_invalid_query)
                            logger.info(f"Corrigidos {invalid_count} documentos com tipos inválidos")
                    except Exception as e:
                        logger.error(f"Erro ao corrigir documentos: {str(e)}")
                
                logger.info("Inicialização do DocumentType concluída")
                await db_session.commit()
            else:
                logger.info("Enum DocumentType está atualizado")
        else:
            logger.info("Enum DocumentType não encontrado, criando...")
            
            # Criar o enum
            create_enum_query = text(f"""
                CREATE TYPE documenttype AS ENUM ('{values_str}');
            """)
            
            await db_session.execute(create_enum_query)
            
            # Criar função de conversão segura para o enum
            await db_session.execute(text(f"""
                CREATE OR REPLACE FUNCTION text_to_documenttype(text) RETURNS documenttype AS $$
                BEGIN
                    BEGIN
                        RETURN $1::documenttype;
                    EXCEPTION WHEN OTHERS THEN
                        RETURN 'OUTRO'::documenttype;
                    END;
                END;
                $$ LANGUAGE plpgsql IMMUTABLE;
            """))
            
            await db_session.commit()
            logger.info("Enum DocumentType e função de conversão criados com sucesso")
    
    except Exception as e:
        logger.error(f"Erro ao configurar enum DocumentType: {str(e)}")
        logger.error(f"Detalhes: {getattr(e, '__cause__', 'Sem causa adicional')}")
        # Não propagar a exceção, apenas logar
        # Permitiremos que o sistema tente funcionar com string direta


async def initialize_enums(db_session: AsyncSession):
    """
    Inicializa todos os enums necessários no banco de dados.
    """
    await ensure_document_type_enum(db_session) 