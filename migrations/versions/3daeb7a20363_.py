"""empty message

Revision ID: 3daeb7a20363
Revises: 14b29768b468
Create Date: 2015-03-29 21:00:07.008738

"""

# revision identifiers, used by Alembic.
revision = '3daeb7a20363'
down_revision = '14b29768b468'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('item', sa.Column('ingredients', sa.String(length=500), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('item', 'ingredients')
    ### end Alembic commands ###