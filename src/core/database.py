"""PostgreSQL database client and persistence layer for BayanSafe.

Connects to the PostgreSQL database defined in .env, supporting player accounts,
stage progression, runs, high scores, achievements, and disaster quiz questions.
"""
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded from project root
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

logger = logging.getLogger("bayansafe.database")

# Try to import psycopg2
try:
    import psycopg2
    from psycopg2 import pool
    import psycopg2.errors
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 is not installed or available.")


class DatabaseManager:
    """Manages PostgreSQL connection and operations for BayanSafe."""

    def __init__(self):
        self._pool = None
        self._connected = False
        self._init_connection()

    def _init_connection(self):
        """Attempt to initialize connection to PostgreSQL using .env credentials."""
        if not PSYCOPG2_AVAILABLE:
            self._connected = False
            return

        try:
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "5432")
            dbname = os.getenv("DB_NAME", "bayansafe")
            user = os.getenv("DB_USER", "bayan_api")
            password = os.getenv("DB_PASSWORD", "")

            # Test connection
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
                connect_timeout=3
            )
            conn.close()
            self._connected = True
            logger.info("Database connection established successfully.")
        except Exception as e:
            self._connected = False
            logger.warning(f"Could not connect to database: {e}")

    @property
    def is_connected(self) -> bool:
        """Return True if PostgreSQL database is reachable."""
        return self._connected

    def get_connection(self):
        """Return a fresh raw connection from .env settings."""
        if not PSYCOPG2_AVAILABLE:
            raise RuntimeError("psycopg2 is not available")
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "bayansafe"),
            user=os.getenv("DB_USER", "bayan_api"),
            password=os.getenv("DB_PASSWORD", ""),
            connect_timeout=3
        )

    def test_connection(self) -> Tuple[bool, str]:
        """Test connection and return status and descriptive message."""
        if not PSYCOPG2_AVAILABLE:
            return False, "psycopg2 library is not installed"
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                ver = cur.fetchone()[0]
            conn.close()
            self._connected = True
            return True, f"Connected to PostgreSQL: {ver}"
        except Exception as e:
            self._connected = False
            return False, str(e)

    # -------------------------------------------------------------------------
    # Player Management
    # -------------------------------------------------------------------------
    def get_or_create_player(self, username: str, character_id: Optional[str] = "juan") -> Optional[Dict[str, Any]]:
        """Retrieve existing player by username, or create if not present."""
        if not self._connected:
            return None
        try:
            conn = self.get_connection()
            with conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT player_id, username, character_id, play_seconds FROM players WHERE username = %s",
                    (username,)
                )
                row = cur.fetchone()
                if row:
                    player_id, uname, char_id, play_s = row
                    cur.execute("UPDATE players SET last_played_at = NOW() WHERE player_id = %s", (player_id,))
                else:
                    cur.execute(
                        """INSERT INTO players (username, character_id, created_at, last_played_at, play_seconds)
                           VALUES (%s, %s, NOW(), NOW(), 0) RETURNING player_id, username, character_id, play_seconds""",
                        (username, character_id)
                    )
                    player_id, uname, char_id, play_s = cur.fetchone()

                    # Initialize stage 1 (home_island_tutorial or earthquake) as UNLOCKED
                    cur.execute(
                        """INSERT INTO player_stage_progress (player_id, stage_id, status)
                           VALUES (%s, 'home_island_tutorial', 'UNLOCKED'), (%s, 'earthquake', 'UNLOCKED')
                           ON CONFLICT DO NOTHING""",
                        (player_id, player_id)
                    )
            conn.close()
            return {
                "player_id": player_id,
                "username": uname,
                "character_id": char_id,
                "play_seconds": play_s
            }
        except Exception as e:
            logger.error(f"Error getting/creating player: {e}")
            return None

    def update_player_character(self, player_id: int, character_id: str) -> bool:
        """Update selected hero character for player."""
        if not self._connected:
            return False
        try:
            conn = self.get_connection()
            with conn, conn.cursor() as cur:
                cur.execute("UPDATE players SET character_id = %s, last_played_at = NOW() WHERE player_id = %s",
                            (character_id, player_id))
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating character: {e}")
            return False

    # -------------------------------------------------------------------------
    # Stage Progression & Runs
    # -------------------------------------------------------------------------
    def load_player_progress(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Load unlocked stages, completed stages, and best records from DB."""
        if not self._connected:
            return None
        try:
            conn = self.get_connection()
            with conn, conn.cursor() as cur:
                cur.execute("SELECT character_id, username FROM players WHERE player_id = %s", (player_id,))
                p_row = cur.fetchone()
                if not p_row:
                    conn.close()
                    return None
                char_id, username = p_row

                cur.execute(
                    """SELECT stage_id, status, best_time_s, best_score, perfect
                       FROM player_stage_progress WHERE player_id = %s""",
                    (player_id,)
                )
                unlocked = set()
                completed = set()
                records = {}
                for stage_id, status, best_time, best_score, perfect in cur.fetchall():
                    if status in ('UNLOCKED', 'COMPLETED'):
                        unlocked.add(stage_id)
                    if status == 'COMPLETED':
                        completed.add(stage_id)
                    records[stage_id] = {
                        "best_time": best_time,
                        "best_score": best_score or 0,
                        "perfect": bool(perfect)
                    }

                cur.execute("SELECT achievement_id FROM player_achievements WHERE player_id = %s", (player_id,))
                achievements = [r[0] for r in cur.fetchall()]

            conn.close()
            return {
                "player_id": player_id,
                "username": username,
                "character_id": char_id,
                "unlocked": unlocked,
                "completed": completed,
                "records": records,
                "achievements": achievements
            }
        except Exception as e:
            logger.error(f"Error loading player progress: {e}")
            return None

    def record_stage_run(self, player_id: int, stage_id: str, time_seconds: int,
                         score: int, completed: bool, perfect: bool = False,
                         damage_taken: int = 0, objectives_done: int = 0,
                         items_found: int = 0, next_stage_id: Optional[str] = None) -> bool:
        """Record stage run in stage_runs table and update player_stage_progress."""
        if not self._connected:
            return False
        try:
            conn = self.get_connection()
            with conn, conn.cursor() as cur:
                # 1. Insert stage run history
                cur.execute(
                    """INSERT INTO stage_runs
                       (player_id, stage_id, time_seconds, damage_taken, objectives_done, items_found, score, completed, played_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
                    (player_id, stage_id, time_seconds, damage_taken, objectives_done, items_found, score, completed)
                )

                # 2. Update player_stage_progress
                cur.execute(
                    """INSERT INTO player_stage_progress (player_id, stage_id, status, best_time_s, best_score, perfect)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ON CONFLICT (player_id, stage_id) DO UPDATE SET
                           status = CASE WHEN EXCLUDED.status = 'COMPLETED' OR player_stage_progress.status = 'COMPLETED'
                                         THEN 'COMPLETED' ELSE EXCLUDED.status END,
                           best_time_s = LEAST(COALESCE(player_stage_progress.best_time_s, EXCLUDED.best_time_s), EXCLUDED.best_time_s),
                           best_score = GREATEST(COALESCE(player_stage_progress.best_score, 0), EXCLUDED.best_score),
                           perfect = player_stage_progress.perfect OR EXCLUDED.perfect""",
                    (player_id, stage_id, 'COMPLETED' if completed else 'UNLOCKED', time_seconds, score, perfect)
                )

                # 3. Unlock next stage if completed
                if completed and next_stage_id:
                    cur.execute(
                        """INSERT INTO player_stage_progress (player_id, stage_id, status)
                           VALUES (%s, %s, 'UNLOCKED')
                           ON CONFLICT (player_id, stage_id) DO UPDATE SET
                               status = CASE WHEN player_stage_progress.status = 'COMPLETED' THEN 'COMPLETED' ELSE 'UNLOCKED' END""",
                        (player_id, next_stage_id)
                    )

                # 4. Update player's last played time
                cur.execute("UPDATE players SET last_played_at = NOW() WHERE player_id = %s", (player_id,))

            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error recording stage run: {e}")
            return False

    # -------------------------------------------------------------------------
    # Quiz Questions & Answer Logging
    # -------------------------------------------------------------------------
    def get_questions(self, stage_id: str) -> List[Dict[str, Any]]:
        """Fetch disaster questions for a stage."""
        if not self._connected:
            return []
        try:
            conn = self.get_connection()
            with conn, conn.cursor() as cur:
                cur.execute(
                    """SELECT question_id, phase, prompt, option_a, option_b, option_c, option_d, correct, explanation
                       FROM questions WHERE stage_id = %s ORDER BY question_id""",
                    (stage_id,)
                )
                rows = []
                for q_id, phase, prompt, a, b, c, d, correct, expl in cur.fetchall():
                    rows.append({
                        "question_id": q_id,
                        "phase": phase,
                        "prompt": prompt,
                        "options": {"A": a, "B": b, "C": c, "D": d},
                        "correct": correct,
                        "explanation": expl
                    })
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"Error fetching questions: {e}")
            return []

    def log_answer(self, player_id: int, question_id: int, chosen: str, is_correct: bool) -> bool:
        """Log player's answer to answer_log table."""
        if not self._connected:
            return False
        try:
            conn = self.get_connection()
            with conn, conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO answer_log (player_id, question_id, chosen, is_correct, answered_at)
                       VALUES (%s, %s, %s, %s, NOW())""",
                    (player_id, question_id, chosen[:1].upper(), is_correct)
                )
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error logging answer: {e}")
            return False

    # -------------------------------------------------------------------------
    # Leaderboard & High Scores
    # -------------------------------------------------------------------------
    def get_high_scores(self, stage_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top player scores from stage_runs and players table."""
        if not self._connected:
            return []
        try:
            conn = self.get_connection()
            with conn, conn.cursor() as cur:
                if stage_id:
                    cur.execute(
                        """SELECT p.username, r.stage_id, r.score, r.time_seconds, r.played_at
                           FROM stage_runs r
                           JOIN players p ON r.player_id = p.player_id
                           WHERE r.stage_id = %s AND r.completed = true
                           ORDER BY r.score DESC, r.time_seconds ASC
                           LIMIT %s""",
                        (stage_id, limit)
                    )
                else:
                    cur.execute(
                        """SELECT p.username, r.stage_id, MAX(r.score) as best_score, MIN(r.time_seconds) as best_time
                           FROM stage_runs r
                           JOIN players p ON r.player_id = p.player_id
                           WHERE r.completed = true
                           GROUP BY p.username, r.stage_id
                           ORDER BY best_score DESC
                           LIMIT %s""",
                        (limit,)
                    )
                rows = []
                for row in cur.fetchall():
                    if stage_id:
                        rows.append({
                            "username": row[0],
                            "stage_id": row[1],
                            "score": row[2],
                            "time": row[3],
                            "date": str(row[4])
                        })
                    else:
                        rows.append({
                            "username": row[0],
                            "stage_id": row[1],
                            "score": row[2],
                            "time": row[3]
                        })
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"Error fetching high scores: {e}")
            return []


# Singleton instance
db_manager = DatabaseManager()
