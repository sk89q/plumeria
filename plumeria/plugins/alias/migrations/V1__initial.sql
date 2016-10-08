CREATE TABLE alias_aliases (
  id        INT           NOT NULL AUTO_INCREMENT,
  transport VARCHAR(100)  NOT NULL,
  server    VARCHAR(100)  NOT NULL,
  alias     VARCHAR(100)  NOT NULL,
  command   VARCHAR(2000) NOT NULL,
  PRIMARY KEY (id)
)
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE INDEX idx_alias_aliases_transport
  ON alias_aliases (transport);

CREATE INDEX idx_alias_aliases_transport_server
  ON alias_aliases (transport, server);

ALTER TABLE alias_aliases
  ADD CONSTRAINT ux_alias_aliases_transport_server_alias UNIQUE (transport, server, alias);
