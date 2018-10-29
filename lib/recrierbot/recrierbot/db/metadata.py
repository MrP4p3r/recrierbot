import sqlalchemy as sa


meta = sa.MetaData()

chat_token_t = sa.Table(
    'chattoken', meta,

    sa.Column('chat_id', sa.BIGINT),
    sa.Column('token', sa.CHAR(32)),

    sa.PrimaryKeyConstraint('chat_id', 'token'),
    sa.Index('chattoken_token', 'token', unique=True),
)
