CREATE TABLE IF NOT EXISTS plumeria_migrations (
  plugin  VARCHAR(100) NOT NULL PRIMARY KEY,
  version INTEGER      NOT NULL,
  name    VARCHAR(100) NOT NULL
)
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
