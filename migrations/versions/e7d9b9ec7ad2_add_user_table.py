"""add_user_table

Revision ID: e7d9b9ec7ad2
Revises: 1231045cb8e8
Create Date: 2025-11-13 13:13:59.795929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'e7d9b9ec7ad2'
down_revision: Union[str, None] = '1231045cb8e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
