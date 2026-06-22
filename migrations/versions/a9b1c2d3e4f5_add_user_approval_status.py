"""add user approval status

Revision ID: a9b1c2d3e4f5
Revises: f68aee30db8d
Create Date: 2026-05-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'a9b1c2d3e4f5'
down_revision = 'f68aee30db8d'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column['name'] for column in inspect(bind).get_columns('users')}

    if 'is_approved' not in columns:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('is_approved', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    op.execute(sa.text('UPDATE users SET is_approved = true'))

    op.alter_column('users', 'is_approved', server_default=None)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_approved')
