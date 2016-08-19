CREATE TABLE `alias` (
  `server_id` varchar(255) NOT NULL,
  `alias` varchar(255) NOT NULL,
  `command` text NOT NULL,
  PRIMARY KEY (`server_id`,`alias`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
