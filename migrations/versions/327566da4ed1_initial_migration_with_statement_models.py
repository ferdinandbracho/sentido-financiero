"""Initial migration with statement models

Revision ID: 327566da4ed1
Revises: 
Create Date: 2025-06-06 16:58:20.514144

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '327566da4ed1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create bank_statements table
    op.create_table('bank_statements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('bank_name', sa.String(length=100), nullable=True),
        sa.Column('account_holder', sa.String(length=255), nullable=True),
        sa.Column('account_number', sa.String(length=50), nullable=True),
        sa.Column('statement_period_start', sa.DateTime(), nullable=True),
        sa.Column('statement_period_end', sa.DateTime(), nullable=True),
        sa.Column('upload_date', sa.DateTime(), nullable=False),
        sa.Column('processing_status', sa.String(length=50), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('total_transactions', sa.Integer(), nullable=True),
        sa.Column('total_credits', sa.Float(), nullable=True),
        sa.Column('total_debits', sa.Float(), nullable=True),
        sa.Column('raw_extracted_data', sa.Text(), nullable=True),
        sa.Column('processing_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create category_rules table
    op.create_table('category_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('pattern', sa.String(length=500), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_name')
    )

    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('statement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('processing_date', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('categorization_method', sa.String(length=50), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('is_transfer', sa.Boolean(), nullable=True),
        sa.Column('merchant_name', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('raw_description', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['statement_id'], ['bank_statements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create processing_logs table
    op.create_table('processing_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('statement_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('operation_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('additional_data', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['statement_id'], ['bank_statements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('processing_logs')
    op.drop_table('transactions')
    op.drop_table('category_rules')
    op.drop_table('bank_statements')
