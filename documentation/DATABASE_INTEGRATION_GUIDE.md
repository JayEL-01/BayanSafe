# BayanSafe PostgreSQL Database Integration Guide

This guide explains the database architecture, schema, configuration, and verification procedures for the BayanSafe project.

---

## 1. Connection Configuration

The PostgreSQL connection is configured through the project root `.env` file:

```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bayansafe
DB_USER=bayan_api
DB_PASSWORD=12345678
```

The database credentials are never hardcoded in game source code. The singleton `DatabaseManager` in `src/core/database.py` (and `core/database.py`) loads these variables using `python-dotenv`.

---

## 2. Database Schema Reference

The database operates on PostgreSQL with the following tables (defined in `database/schema.sql`):

### `players`
Stores registered player accounts and character choices.
- `player_id` (SERIAL PRIMARY KEY)
- `username` (VARCHAR(50) UNIQUE NOT NULL)
- `email` (VARCHAR(100))
- `pin_hash` (VARCHAR(255))
- `card_hash` (CHAR(64) UNIQUE) - Optional RFID card hash
- `character_id` (VARCHAR(30)) - 'juan' or 'maria'
- `created_at` (TIMESTAMP)
- `last_played_at` (TIMESTAMP)
- `play_seconds` (INT)

### `player_stage_progress`
Tracks per-stage unlock status, high scores, and best times.
- `player_id` (INT REFERENCES players)
- `stage_id` (VARCHAR(30)) - e.g. 'home_island_tutorial', 'earthquake'
- `status` (VARCHAR(10)) - 'LOCKED', 'UNLOCKED', 'COMPLETED'
- `best_time_s` (INT)
- `best_score` (INT)
- `perfect` (BOOLEAN)
- `PRIMARY KEY (player_id, stage_id)`

### `stage_runs`
Maintains historical attempt logs for every finished stage.
- `run_id` (SERIAL PRIMARY KEY)
- `player_id` (INT REFERENCES players)
- `stage_id` (VARCHAR(30))
- `time_seconds` (INT)
- `damage_taken` (INT)
- `objectives_done` (INT)
- `items_found` (INT)
- `score` (INT)
- `completed` (BOOLEAN)
- `played_at` (TIMESTAMP)

### `player_achievements`
Records unlocked badges and milestone achievements.
- `player_id` (INT REFERENCES players)
- `achievement_id` (VARCHAR(50))
- `unlocked_at` (TIMESTAMP)
- `PRIMARY KEY (player_id, achievement_id)`

### `questions`
Contains disaster preparedness scenario quiz questions.
- `question_id` (SERIAL PRIMARY KEY)
- `stage_id` (VARCHAR(30))
- `phase` ('BEFORE', 'DURING', 'AFTER')
- `prompt` (TEXT)
- `option_a`, `option_b`, `option_c`, `option_d` (TEXT)
- `correct` (CHAR(1))
- `explanation` (TEXT)

### `answer_log`
Logs player quiz answers.
- `log_id` (SERIAL PRIMARY KEY)
- `player_id` (INT REFERENCES players)
- `question_id` (INT REFERENCES questions)
- `chosen` (CHAR(1))
- `is_correct` (BOOLEAN)
- `answered_at` (TIMESTAMP)

---

## 3. How Game Session Synchronizes with PostgreSQL

1. **Dual Persistence Model**:
   - The game utilizes a local-first + PostgreSQL synchronized architecture.
   - When offline or without a database, save data is written atomically to `progress.json`.
   - When PostgreSQL is running, `GameSession` automatically synchronizes every action:
     * `load()`: Merges unlocked stages and high scores from `player_stage_progress`.
     * `complete_stage()`: Sets status to `'COMPLETED'` in PostgreSQL and unlocks the next stage.
     * `record_run()`: Inserts a run row into `stage_runs` and updates personal bests.

2. **World Map Progression**:
   - The World Map reads checkpoint states directly from `session.unlocked` and `session.completed`, reflecting database updates immediately.

---

## 4. How to Verify Database Connectivity

Run the automated database integration suite:
```bash
python tools/test_db_integration.py
```

Expected output:
```text
Testing DB connection...
Testing get_or_create_player...
Player created/retrieved: {'player_id': 1, 'username': 'TestPlayer', ...}
Testing update_player_character...
Testing record_stage_run...
Testing load_player_progress...
Loaded progress: {'unlocked': {'home_island_tutorial', 'earthquake'}, 'completed': {'home_island_tutorial'}, ...}
Testing high scores...
Top scores: [...]
Testing quiz questions...
Retrieved 3 questions for typhoon
Testing answer logging...
ALL DB OPERATIONS TESTED AND PASSED 100%!
```
