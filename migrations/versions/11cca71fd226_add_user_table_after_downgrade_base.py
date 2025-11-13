"""add_user_table_after_downgrade_base

Revision ID: 11cca71fd226
Revises: e7d9b9ec7ad2
Create Date: 2025-11-13 13:53:04.986970

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '11cca71fd226'
down_revision: Union[str, None] = 'e7d9b9ec7ad2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
