"""Initial migration.

Revision ID: 1ed2d19c24fa
Revises: 
Create Date: 2021-06-25 08:25:58.964562

"""
from alembic import op
import sqlalchemy as sa

from team_picker import UNASSIGNED_TEAM_NAME, PRE_CONFIG_ROLE_NAMES

# revision identifiers, used by Alembic.

revision = '1ed2d19c24fa'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=80), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('teams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('name')
    )
    op.create_table('matches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('home_id', sa.Integer(), nullable=False),
    sa.Column('away_id', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.Column('result', sa.Boolean(), nullable=False),
    sa.Column('score_home', sa.Integer(), nullable=False),
    sa.Column('score_away', sa.Integer(), nullable=False),
    sa.CheckConstraint('home_id != away_id', name='different_teams_check'),
    sa.ForeignKeyConstraint(['away_id'], ['teams.id'], ),
    sa.ForeignKeyConstraint(['home_id'], ['teams.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('away_id', 'start_time', name='uq_away_fixture'),
    sa.UniqueConstraint('home_id', 'away_id', 'start_time', name='uq_duplicate_match_home_venue'),
    sa.UniqueConstraint('home_id', 'start_time', name='uq_home_fixture')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('surname', sa.String(length=80), nullable=False),
    sa.Column('auth0_id', sa.String(length=80), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('auth0_id'),
    sa.UniqueConstraint('auth0_id')
    )
    op.create_table('selections',
    sa.Column('match_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('confirmed', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('match_id', 'user_id')
    )
    # ### end Alembic commands ###

    # pre-populate roles
    roles = sa.table('roles',
                      sa.column('role', sa.String),
                      )
    op.bulk_insert(roles,
                   [
                       {'role': name} for name in PRE_CONFIG_ROLE_NAMES
                   ]
                   )
    # pre-populate teams
    teams = sa.table('teams',
                      sa.column('name', sa.String),
                      )
    op.bulk_insert(teams,
                   [
                       {'name': UNASSIGNED_TEAM_NAME},
                   ]
                   )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('selections')
    op.drop_table('users')
    op.drop_table('matches')
    op.drop_table('teams')
    op.drop_table('roles')
    # ### end Alembic commands ###
