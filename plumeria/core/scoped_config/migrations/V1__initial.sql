CREATE TABLE config_values (
  id        INT           NOT NULL AUTO_INCREMENT,
  transport VARCHAR(100)  NOT NULL,
  server    VARCHAR(100)  NOT NULL,
  channel   VARCHAR(100)  NULL,
  section   VARCHAR(120)  NOT NULL,
  `key`     VARCHAR(120)  NOT NULL,
  value     VARCHAR(2000) NOT NULL,
  PRIMARY KEY (id)
)
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE INDEX idx_config_values_transport
  ON config_values (transport);

CREATE INDEX idx_config_values_transport_server_channel
  ON config_values (transport, server, channel);

ALTER TABLE config_values
  ADD CONSTRAINT ux_config_values_keys UNIQUE (transport, server, channel, section, `key`);
