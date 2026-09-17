"""advanced evaluation and error analysis schema

Revision ID: 003_advanced_evaluation_schema
Revises: 002_gamification_schema
Create Date: 2026-09-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_advanced_evaluation_schema'
down_revision = '002_gamification_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Practice attempts columns
    op.add_column('practice_attempts', sa.Column('errors', sa.JSON(), nullable=True))
    op.add_column('practice_attempts', sa.Column('cefr_level', sa.String(length=10), nullable=True))
    op.add_column('practice_attempts', sa.Column('actionable_tips', sa.JSON(), nullable=True))

    # Multi-word practice attempts columns
    op.add_column('multi_word_practice_attempts', sa.Column('errors', sa.JSON(), nullable=True))
    op.add_column('multi_word_practice_attempts', sa.Column('cefr_level', sa.String(length=10), nullable=True))
    op.add_column('multi_word_practice_attempts', sa.Column('actionable_tips', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('multi_word_practice_attempts', 'actionable_tips')
    op.drop_column('multi_word_practice_attempts', 'cefr_level')
    op.drop_column('multi_word_practice_attempts', 'errors')

    op.drop_column('practice_attempts', 'actionable_tips')
    op.drop_column('practice_attempts', 'cefr_level')
    op.drop_column('practice_attempts', 'errors')
