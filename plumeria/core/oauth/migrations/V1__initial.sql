CREATE TABLE oauth_tokens (
  id            INT          NOT NULL         AUTO_INCREMENT,
  transport     VARCHAR(100) NOT NULL,
  user          VARCHAR(100) NOT NULL,
  endpoint      VARCHAR(100) NOT NULL,
  access_token  VARCHAR(300) NOT NULL,
  token_type    VARCHAR(100) NOT NULL,
  expiration_at DATETIME     NOT NULL,
  refresh_token VARCHAR(300) NOT NULL,
  PRIMARY KEY (id)
)
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE INDEX idx_oauth_tokens_transport
  ON oauth_tokens (transport);

CREATE INDEX idx_oauth_tokens_transport_user
  ON oauth_tokens (transport, user);

CREATE INDEX idx_oauth_tokens_endpoint
  ON oauth_tokens (endpoint);

CREATE INDEX idx_oauth_tokens_transport_user_endpoint
  ON oauth_tokens (transport, user, endpoint);

ALTER TABLE oauth_tokens
  ADD CONSTRAINT ux_oauth_tokens_keys UNIQUE (transport, user, endpoint);
