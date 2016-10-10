CREATE TABLE prefs_values (
  id         INT           NOT NULL         AUTO_INCREMENT,
  transport  VARCHAR(100)  NOT NULL,
  user       VARCHAR(100)  NOT NULL,
  name       VARCHAR(120)  NOT NULL,
  value      VARCHAR(2000) NOT NULL,
  PRIMARY KEY (id)
)
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE INDEX idx_prefs_values_transport
  ON prefs_values (transport);

CREATE INDEX idx_prefs_values_transport_user
  ON prefs_values (transport, user);

ALTER TABLE prefs_values
  ADD CONSTRAINT ux_prefs_values_keys UNIQUE (transport, user, name);
