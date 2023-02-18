--
-- File generated with SQLiteStudio v3.4.3 on Sat Feb 18 15:35:42 2023
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: users_conversation
CREATE TABLE IF NOT EXISTS users_conversation (
    user_id            TEXT (32) UNIQUE ON CONFLICT REPLACE,
    conversation_state TEXT
);


-- Table: users_mass
CREATE TABLE IF NOT EXISTS users_mass (
    record_id INTEGER,
    user_id   TEXT (32),
    date      DATE      NOT NULL,
    body_mass REAL,
    PRIMARY KEY (
        record_id AUTOINCREMENT
    ),
    CONSTRAINT user_date_constraint UNIQUE (
        user_id,
        date
    )
    ON CONFLICT REPLACE
);


-- Index: user_id_idx
CREATE INDEX IF NOT EXISTS user_id_idx ON users_mass (
    user_id
);


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
