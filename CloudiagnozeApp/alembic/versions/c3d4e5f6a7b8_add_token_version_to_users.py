"""add token_version to users

Revision ID: c3d4e5f6a7b8
Revises: f5dd5cfaf313
Create Date: 2026-06-19 00:00:00.000000

Ajoute token_version sur la table users pour permettre la révocation
des tokens JWT au logout et lors d'un changement de mot de passe.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'f5dd5cfaf313'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'token_version',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment="Incrémentée au logout/changement de mdp — invalide les anciens tokens",
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'token_version')
