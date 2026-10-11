CREATE USER bayan_api WITH PASSWORD 'change-this-password';
GRANT ALL PRIVILEGES ON DATABASE bayansafe TO bayan_api;



-- BayanSafe schema (PostgreSQL)

CREATE TABLE players (
    player_id      SERIAL PRIMARY KEY,
    username       VARCHAR(50) UNIQUE NOT NULL,
    email          VARCHAR(100),
    pin_hash       VARCHAR(255),            -- login without a card
    card_hash      CHAR(64) UNIQUE,         -- SHA-256 of the RFID UID
    character_id   VARCHAR(30),
    created_at     TIMESTAMP DEFAULT NOW(),
    last_played_at TIMESTAMP,
    play_seconds   INT DEFAULT 0
);

CREATE TABLE player_stage_progress (
    player_id   INT REFERENCES players ON DELETE CASCADE,
    stage_id    VARCHAR(30),
    status      VARCHAR(10) DEFAULT 'LOCKED'
                CHECK (status IN ('LOCKED','UNLOCKED','COMPLETED')),
    best_time_s INT,
    best_score  INT,
    perfect     BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (player_id, stage_id)
);

CREATE TABLE player_achievements (
    player_id      INT REFERENCES players ON DELETE CASCADE,
    achievement_id VARCHAR(50),
    unlocked_at    TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (player_id, achievement_id)
);

-- One row per finished attempt. Records are queried from here.
CREATE TABLE stage_runs (
    run_id          SERIAL PRIMARY KEY,
    player_id       INT REFERENCES players ON DELETE CASCADE,
    stage_id        VARCHAR(30),
    time_seconds    INT,
    damage_taken    INT,
    objectives_done INT,
    items_found     INT,
    score           INT,
    completed       BOOLEAN,
    played_at       TIMESTAMP DEFAULT NOW()
);

-- Quiz questions (your proposal lists "scenario questions")
CREATE TABLE questions (
    question_id SERIAL PRIMARY KEY,
    stage_id    VARCHAR(30) NOT NULL,
    phase       VARCHAR(10) CHECK (phase IN ('BEFORE','DURING','AFTER')),
    prompt      TEXT NOT NULL,
    option_a    TEXT NOT NULL,
    option_b    TEXT NOT NULL,
    option_c    TEXT,
    option_d    TEXT,
    correct     CHAR(1) NOT NULL CHECK (correct IN ('A','B','C','D')),
    explanation TEXT
);

-- Game log: every answer a player gives
CREATE TABLE answer_log (
    log_id      SERIAL PRIMARY KEY,
    player_id   INT REFERENCES players ON DELETE CASCADE,
    question_id INT REFERENCES questions,
    chosen      CHAR(1),
    is_correct  BOOLEAN,
    answered_at TIMESTAMP DEFAULT NOW()
);

-- Let the API user use everything above
GRANT ALL ON ALL TABLES IN SCHEMA public TO bayan_api;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO bayan_api;