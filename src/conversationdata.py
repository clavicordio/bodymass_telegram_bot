import aiosqlite

sqlite_db_path = 'data/bodymass.sqlite'
sqlite_db_users_conversation = 'users_conversation'


class ConversationState:
    init = 'init'
    awaiting_body_weight = 'awaiting_body_weight'
    awaiting_erase_confirmation = 'awaiting_erase_confirmation'
    awaiting_csv_table = 'awaiting_csv_table'


conversation_states = [k for k in vars(ConversationState).keys() if not k.startswith('_')]

for k, v in vars(ConversationState).items():
    if not k.startswith('_'):
        assert k == v


async def get_conversation_data(user_id: int) -> dict:
    async with aiosqlite.connect(sqlite_db_path) as db:
        async with db.cursor() as cursor:
            query = f"SELECT conversation_state FROM {sqlite_db_users_conversation} " \
                                 f"WHERE user_id = '{user_id}';"
            await cursor.execute(query)
            conversation_state = await cursor.fetchone()
            conversation_state = conversation_state[0] if conversation_state is not None else 'init'
            assert conversation_state in conversation_states
            return {'conversation_state': conversation_state}


async def write_conversation_data(user_id: int, conversation_data: dict) -> None:
    async with aiosqlite.connect(sqlite_db_path) as db:

        query = f"INSERT INTO {sqlite_db_users_conversation} (user_id, conversation_state) " \
                f"VALUES ('{user_id}', '{conversation_data['conversation_state']}'); "

        await db.execute(query)
        await db.commit()

