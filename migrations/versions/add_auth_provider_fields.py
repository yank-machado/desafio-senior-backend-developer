"""add auth provider fields

Revision ID: add_auth_provider_fields
Revises: 2f02c8adf67b
Create Date: 2023-12-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_auth_provider_fields'
down_revision = '2f02c8adf67b'  # Apontando para a migração anterior de MFA
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar tipo enum para AuthProvider
    auth_provider_enum = postgresql.ENUM('LOCAL', 'GOOGLE', 'FACEBOOK', name='authprovider')
    auth_provider_enum.create(op.get_bind())
    
    # Adicionar coluna auth_provider
    op.add_column('users', sa.Column('auth_provider', 
                  sa.Enum('LOCAL', 'GOOGLE', 'FACEBOOK', name='authprovider'),
                  server_default='LOCAL', nullable=False))
    
    # Adicionar coluna profile_picture
    op.add_column('users', sa.Column('profile_picture', sa.String(), nullable=True))


def downgrade() -> None:
    # Remover colunas
    op.drop_column('users', 'profile_picture')
    op.drop_column('users', 'auth_provider')
    
    # Remover tipo enum
    op.execute('DROP TYPE authprovider') 