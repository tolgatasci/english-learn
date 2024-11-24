"""
Revision ID: f106c79f900c
Revises:
Create Date: 2024-11-15 21:28:48.084432
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f106c79f900c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        # Add the part_of_speech column if it doesn't exist
        op.add_column('words', sa.Column('part_of_speech', sa.String(20), nullable=False, server_default='other'))
    except sa.exc.OperationalError as e:
        # Ignore the error if the column already exists
        if "Duplicate column name 'part_of_speech'" not in str(e):
            raise e

    # Update existing 'article' values to 'determiner'
    op.execute("""
        UPDATE words
        SET part_of_speech = 'determiner'
        WHERE part_of_speech = 'article'
    """)


def downgrade() -> None:
    # Revert 'determiner' values back to 'article'
    op.execute("""
        UPDATE words
        SET part_of_speech = 'article'
        WHERE part_of_speech = 'determiner'
    """)

    try:
        # Drop the part_of_speech column if it exists
        op.drop_column('words', 'part_of_speech')
    except sa.exc.OperationalError as e:
        # Ignore the error if the column doesn't exist
        if "Unknown column 'part_of_speech' in 'field list'" not in str(e):
            raise e