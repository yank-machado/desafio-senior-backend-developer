from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from core.entities.user import User
from core.interfaces.repositories import UserRepository
from infrastucture.database.models import UserModel

logger = logging.getLogger(__name__)

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, user: User) -> User:
        try:
            db_user = UserModel(
                id=user.id,
                email=user.email,
                hashed_password=user.hashed_password,
                is_active=user.is_active,
                is_admin=user.is_admin,
                mfa_enabled=user.mfa_enabled,
                mfa_secret=user.mfa_secret
            )
            
            self.session.add(db_user)
            
            try:
                await self.session.flush()
                logger.info(f"Usuário criado: id={user.id}")
            except Exception as db_error:
                error_msg = str(db_error)
                
                if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower():
                    logger.error(f"Erro de violação de unicidade: {user.email}")
                    raise ValueError(f"Usuário com este email já existe: {user.email}")
                elif "connection" in error_msg.lower():
                    logger.error(f"Erro de conexão com banco de dados")
                    raise ValueError("Erro de conexão com o banco de dados")
                
                raise
            
            return self._map_to_entity(db_user)
            
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {str(e)}")
            raise
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        try:
            query = select(UserModel).where(UserModel.id == user_id)
            
            try:
                result = await self.session.execute(query)
                db_user = result.scalars().first()
            except Exception as query_error:
                logger.error(f"Erro na consulta por ID: {str(query_error)}")
                raise
            
            if not db_user:
                return None
            
            return self._map_to_entity(db_user)
            
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por ID: {str(e)}")
            raise
    
    async def get_by_email(self, email: str) -> Optional[User]:
        try:
            query = select(UserModel).where(UserModel.email == email)
            
            try:
                result = await self.session.execute(query)
                db_user = result.scalars().first()
            except Exception as query_error:
                logger.error(f"Erro na consulta por email: {str(query_error)}")
                raise
            
            if not db_user:
                return None
            
            return self._map_to_entity(db_user)
            
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por email: {str(e)}")
            raise
    
    async def update(self, user: User) -> User:
        try:
            query = select(UserModel).where(UserModel.id == user.id)
            result = await self.session.execute(query)
            db_user = result.scalars().first()
            
            if db_user:
                db_user.email = user.email
                db_user.hashed_password = user.hashed_password
                db_user.is_active = user.is_active
                db_user.is_admin = user.is_admin
                db_user.mfa_enabled = user.mfa_enabled
                db_user.mfa_secret = user.mfa_secret
                
                try:
                    await self.session.flush()
                    logger.info(f"Usuário atualizado: id={user.id}")
                except Exception as db_error:
                    logger.error(f"Erro na atualização: {str(db_error)}")
                    raise
                
                return self._map_to_entity(db_user)
            else:
                logger.warning(f"Tentativa de atualizar usuário inexistente: id={user.id}")
                return None
            
        except Exception as e:
            logger.error(f"Erro na atualização: {str(e)}")
            raise
    
    async def delete(self, user_id: UUID) -> bool:
        try:
            query = select(UserModel).where(UserModel.id == user_id)
            result = await self.session.execute(query)
            db_user = result.scalars().first()
            
            if db_user:
                try:
                    await self.session.delete(db_user)
                    await self.session.flush()
                    logger.info(f"Usuário removido: id={user_id}")
                    return True
                except Exception as db_error:
                    logger.error(f"Erro ao remover: {str(db_error)}")
                    raise
            else:
                logger.warning(f"Tentativa de remover usuário inexistente: id={user_id}")
                return False
            
        except Exception as e:
            logger.error(f"Erro na remoção: {str(e)}")
            raise
    
    def _map_to_entity(self, db_user: UserModel) -> User:
        return User(
            id=db_user.id,
            email=db_user.email,
            hashed_password=db_user.hashed_password,
            is_active=db_user.is_active,
            is_admin=db_user.is_admin,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
            mfa_enabled=db_user.mfa_enabled,
            mfa_secret=db_user.mfa_secret
        )