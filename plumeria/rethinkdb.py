from queue import Queue, Empty
import rethinkdb as r
from . import config

MIGRATIONS_TABLE = "plumeria_migrations"

r.set_loop_type('asyncio')

host = config.create("rethinkdb", "host", fallback="localhost")
port = config.create("rethinkdb", "port", type=int, fallback=28015, comment="Default is 28015")
db_name = config.create("rethinkdb", "database", fallback="plumeria")
username = config.create("rethinkdb", "username", fallback="admin")
password = config.create("rethinkdb", "password", fallback="")
timeout = config.create("rethinkdb", "connection_timeout", type=int, fallback=3)


class PooledConnection:
    """Context manager for RethinkDB pooled connections."""

    def __init__(self, pool):
        self.pool = pool
        self.conn = None

    async def __aenter__(self):
        self.conn = await self.pool.get_connection()
        return self.conn

    async def __aexit__(self, *exc):
        self.pool.queue.put(self.conn)


class RethinkDBPool:
    """Keeps a pool of RethinkDB connections and makes one when needed."""

    def __init__(self):
        self.queue = Queue()

    def open(self):
        return PooledConnection(self)

    async def get_connection(self):
        while True:
            try:
                conn = self.queue.get(block=False)
                if conn.is_open():
                    return conn
            except Empty as e:
                conn = await r.connect(host=host(), port=port(), db=db_name(), user=username(), password=password(),
                                       timeout=timeout())
                conn.use(db_name())
                return conn


class MigrationsManager:
    def __init__(self, pool):
        self.pool = pool
        self.table_created = False

    async def migrate(self, module, plan):
        async with pool.open() as conn:
            if not self.table_created:
                if not await r.table_list().contains(MIGRATIONS_TABLE).run(conn):
                    await r.table_create(MIGRATIONS_TABLE).run(conn)
                self.table_created = True

            cursor = await r.table(MIGRATIONS_TABLE).filter({"module": module}).run(conn)
            if await cursor.fetch_next():
                row = await cursor.next()
                version = row["version"]
            else:
                version = -1
                await r.table(MIGRATIONS_TABLE).insert({
                    "module": module,
                    "version": version,
                    "name": None}).run(conn)

            for index, (name, func) in enumerate(plan):
                if index > version:
                    await func(conn)
                    await r.table(MIGRATIONS_TABLE).filter({"module": module}).update({
                        "version": index,
                        "name": name
                    }).run(conn)


pool = RethinkDBPool()
migrations = MigrationsManager(pool)
