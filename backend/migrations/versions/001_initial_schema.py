"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-09-08 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('english_level', sa.String(length=20), nullable=False, server_default='intermediate'),
        sa.Column('daily_goal', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('xp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_active_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Vocabulary table
    op.create_table(
        'vocabulary',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('word', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='new'),
        sa.Column('mastery_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('practice_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_recall_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_practiced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_review_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_interval_days', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'word', name='uq_user_word')
    )
    op.create_index(op.f('ix_vocabulary_user_id'), 'vocabulary', ['user_id'], unique=False)
    op.create_index(op.f('ix_vocabulary_word'), 'vocabulary', ['word'], unique=False)
    op.create_index(op.f('ix_vocabulary_status'), 'vocabulary', ['status'], unique=False)
    op.create_index(op.f('ix_vocabulary_next_review_at'), 'vocabulary', ['next_review_at'], unique=False)

    # Word Details table
    op.create_table(
        'word_details',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('vocabulary_id', sa.String(length=36), nullable=False),
        sa.Column('simple_meaning', sa.Text(), nullable=False),
        sa.Column('contextual_meaning', sa.Text(), nullable=True),
        sa.Column('part_of_speech', sa.String(length=30), nullable=True),
        sa.Column('pronunciation_text', sa.String(length=100), nullable=True),
        sa.Column('synonyms', sa.JSON(), nullable=False),
        sa.Column('antonyms', sa.JSON(), nullable=False),
        sa.Column('word_forms', sa.JSON(), nullable=False),
        sa.Column('collocations', sa.JSON(), nullable=False),
        sa.Column('cefr_level', sa.String(length=5), nullable=True),
        sa.Column('difficulty_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['vocabulary_id'], ['vocabulary.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vocabulary_id')
    )

    # Vocabulary Examples table
    op.create_table(
        'vocabulary_examples',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('vocabulary_id', sa.String(length=36), nullable=False),
        sa.Column('example_text', sa.Text(), nullable=False),
        sa.Column('context_label', sa.String(length=50), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['vocabulary_id'], ['vocabulary.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vocabulary_examples_vocabulary_id'), 'vocabulary_examples', ['vocabulary_id'], unique=False)


def downgrade() -> None:
    op.drop_table('vocabulary_examples')
    op.drop_table('word_details')
    op.drop_table('vocabulary')
    op.drop_table('users')
