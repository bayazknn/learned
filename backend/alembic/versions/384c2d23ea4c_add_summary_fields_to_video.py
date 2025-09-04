"""add_summary_fields_to_video

Revision ID: 384c2d23ea4c
Revises: 87dacc22b37a
Create Date: 2025-08-31 21:44:41.532624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '384c2d23ea4c'
down_revision: Union[str, Sequence[str], None] = '87dacc22b37a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add summary, summary_processing_status, and summary_processed_at columns to videos table
    op.add_column('videos', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('videos', sa.Column('summary_processing_status', sa.String(), server_default='pending', nullable=True))
    op.add_column('videos', sa.Column('summary_processed_at', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the added columns
    op.drop_column('videos', 'summary_processed_at')
    op.drop_column('videos', 'summary_processing_status')
    op.drop_column('videos', 'summary')
