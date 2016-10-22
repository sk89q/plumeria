import functools
import os.path
import re

import pkg_resources

MIGRATION_FILE_PATTERN = re.compile("^V(?P<version>[0-9]+)__(?P<name>.+)$")


class Version:
    def __init__(self, version, name):
        self.version = version
        self.name = name

    def __str__(self, *args, **kwargs):
        return "v{} ({})".format(self.version, self.name)

    def __repr__(self, *args, **kwargs):
        return self.__str__()


class Migration:
    def __init__(self, version, open):
        self.version = version
        self.open = open

    def __str__(self, *args, **kwargs):
        return str(self.version)

    def __repr__(self, *args, **kwargs):
        return self.__str__()


class MigrationList:
    def __init__(self):
        self.migrations = []

    def load_package(self, pkg):
        migrations = []
        for resource_name in pkg_resources.resource_listdir(pkg, "migrations"):
            name, _ = os.path.splitext(resource_name)
            m = MIGRATION_FILE_PATTERN.match(name)
            if m:
                migration = Migration(Version(int(m.group("version")), m.group("name")),
                                      functools.partial(pkg_resources.resource_stream, pkg,
                                                        "migrations/" + resource_name))
                migrations.append(migration)
        self.migrations = sorted(migrations, key=lambda e: e.version.version)

    def get_migrations(self, current_version: Version = None):
        for migration in self.migrations:
            if current_version and migration.version.version <= current_version.version:
                continue
            else:
                yield migration


class MigrationManager:
    def __init__(self, pool):
        self.pool = pool
        self.versions = {}

    async def setup(self):
        list = MigrationList()
        list.load_package("plumeria.core.storage")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SHOW TABLES LIKE 'plumeria_migrations'")

                if not len(await cur.fetchall()):
                    for migration in list.get_migrations(current_version=None):
                        with migration.open() as f:
                            sql = f.read().decode("utf-8")
                        await cur.execute(sql)

                await cur.execute("SELECT plugin, version, name FROM plumeria_migrations")

                for row in await cur.fetchall():
                    self.versions[row[0]] = Version(row[1], row[2])

    async def migrate_list(self, plugin, migrations):
        current_version = self.versions[plugin] if plugin in self.versions else None
        new_version = current_version

        plan = list(migrations.get_migrations(current_version=current_version))

        if not len(plan):
            return

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                for migration in plan:
                    with migration.open() as f:
                        sql = f.read().decode("utf-8")
                    await cur.execute(sql)
                    new_version = migration.version

            async with conn.cursor() as cur:
                await cur.execute("REPLACE INTO plumeria_migrations (plugin, version, name) VALUES (%s, %s, %s)",
                                  (plugin, new_version.version, new_version.name))
                self.versions[plugin] = new_version

    async def migrate(self, plugin: str, package: str):
        migrations = MigrationList()
        migrations.load_package(package)
        await self.migrate_list(plugin, migrations)
