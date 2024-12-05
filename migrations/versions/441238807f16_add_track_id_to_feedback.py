"""Add track_id to Feedback

Revision ID: 441238807f16
Revises: 
Create Date: 2024-11-15 16:43:46.062743

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '441238807f16'
down_revision = None
branch_labels = None
depends_on = None


# migrations/versions/441238807f16_add_track_id_to_feedback.py
def upgrade():
    with op.batch_alter_table('feedback') as batch_op:
        batch_op.add_column(sa.Column('track_id', sa.String(length=100), nullable=True))

def downgrade():
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        batch_op.drop_column('track_id')
        batch_op.drop_column('track_name')
