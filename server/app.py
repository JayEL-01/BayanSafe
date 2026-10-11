import hashlib
import secrets
from contextlib import contextmanager

import psycopg2.errors
from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_connection

app = Flask(__name__)

STAGES = ["typhoon", "flood", "earthquake", "volcano", "wildfire"]
TOKENS = {}    # login token -> player_id (cleared when the server restarts)


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
@contextmanager
def db():
    """Open a connection, commit on success, roll back on error, always close."""
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            yield cur
    finally:
        conn.close()


def hash_card(uid):
    """Only a hash of the card UID is stored, never the UID itself."""
    return hashlib.sha256(uid.strip().upper().encode()).hexdigest()


def new_token(player_id):
    token = secrets.token_hex(16)
    TOKENS[token] = player_id
    return token


def current_player():
    return TOKENS.get(request.headers.get("X-Token", ""))


def error(message, code=400):
    return jsonify({"ok": False, "error": message}), code


def load_save(cur, player_id):
    cur.execute("SELECT username, character_id FROM players WHERE player_id = %s",
                (player_id,))
    username, character_id = cur.fetchone()
    cur.execute("""SELECT stage_id, status, best_time_s, best_score, perfect
                   FROM player_stage_progress WHERE player_id = %s""", (player_id,))
    stages = {row[0]: {"status": row[1], "best_time": row[2],
                       "best_score": row[3], "perfect": row[4]}
              for row in cur.fetchall()}
    cur.execute("SELECT achievement_id FROM player_achievements WHERE player_id = %s",
                (player_id,))
    achievements = [row[0] for row in cur.fetchall()]
    return {"player_id": player_id, "username": username,
            "character_id": character_id, "stages": stages,
            "achievements": achievements}


# ---------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------
@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    pin = str(data.get("pin", ""))
    if not (3 <= len(username) <= 50):
        return error("Username must be 3 to 50 characters.")
    if len(pin) < 4:
        return error("PIN must be at least 4 characters.")
    try:
        with db() as cur:
            cur.execute("""INSERT INTO players (username, pin_hash)
                           VALUES (%s, %s) RETURNING player_id""",
                        (username, generate_password_hash(pin)))
            player_id = cur.fetchone()[0]
            for number, stage in enumerate(STAGES):
                cur.execute("""INSERT INTO player_stage_progress (player_id, stage_id, status)
                               VALUES (%s, %s, %s)""",
                            (player_id, stage, "UNLOCKED" if number == 0 else "LOCKED"))
            save = load_save(cur, player_id)
    except psycopg2.errors.UniqueViolation:
        return error("That username is already taken.", 409)
    return jsonify({"ok": True, "token": new_token(player_id), "save": save})


@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    with db() as cur:
        cur.execute("SELECT player_id, pin_hash FROM players WHERE username = %s",
                    (str(data.get("username", "")).strip(),))
        row = cur.fetchone()
        if not row or not row[1] or not check_password_hash(row[1], str(data.get("pin", ""))):
            return error("Wrong username or PIN.", 401)
        cur.execute("UPDATE players SET last_played_at = NOW() WHERE player_id = %s", (row[0],))
        save = load_save(cur, row[0])
    return jsonify({"ok": True, "token": new_token(row[0]), "save": save})


# ---------------------------------------------------------------
# RFID cards
# ---------------------------------------------------------------
@app.post("/card/login")
def card_login():
    """The ESP32 or the game sends the card UID. Known card = player + save."""
    uid = str((request.get_json(silent=True) or {}).get("uid", "")).strip()
    if not uid:
        return error("No card UID sent.")
    with db() as cur:
        cur.execute("SELECT player_id FROM players WHERE card_hash = %s", (hash_card(uid),))
        row = cur.fetchone()
        if not row:
            return jsonify({"ok": True, "found": False})
        cur.execute("UPDATE players SET last_played_at = NOW() WHERE player_id = %s", (row[0],))
        save = load_save(cur, row[0])
    return jsonify({"ok": True, "found": True, "token": new_token(row[0]), "save": save})


@app.post("/card/link")
def card_link():
    """A logged-in player links a card to their account."""
    player_id = current_player()
    if not player_id:
        return error("Please log in first.", 401)
    uid = str((request.get_json(silent=True) or {}).get("uid", "")).strip()
    if not uid:
        return error("No card UID sent.")
    try:
        with db() as cur:
            cur.execute("UPDATE players SET card_hash = %s WHERE player_id = %s",
                        (hash_card(uid), player_id))
    except psycopg2.errors.UniqueViolation:
        return error("That card is already linked to another account.", 409)
    return jsonify({"ok": True})


# ---------------------------------------------------------------
# Saving
# ---------------------------------------------------------------
@app.get("/save")
def get_save():
    player_id = current_player()
    if not player_id:
        return error("Please log in first.", 401)
    with db() as cur:
        return jsonify({"ok": True, "save": load_save(cur, player_id)})


@app.post("/save")
def post_save():
    """Called when a stage ends. Records the run and unlocks the next stage."""
    player_id = current_player()
    if not player_id:
        return error("Please log in first.", 401)
    d = request.get_json(silent=True) or {}
    stage = d.get("stage_id")
    if stage not in STAGES:
        return error("Unknown stage.")
    completed = bool(d.get("completed"))
    time_s = int(d.get("time_seconds", 0))
    score = int(d.get("score", 0))
    perfect = bool(d.get("perfect"))

    with db() as cur:
        cur.execute("""INSERT INTO stage_runs
            (player_id, stage_id, time_seconds, damage_taken, objectives_done,
             items_found, score, completed)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (player_id, stage, time_s, int(d.get("damage_taken", 0)),
             int(d.get("objectives_done", 0)), int(d.get("items_found", 0)),
             score, completed))
        if completed:
            cur.execute("""UPDATE player_stage_progress
                SET status = 'COMPLETED',
                    best_time_s = LEAST(COALESCE(best_time_s, %s), %s),
                    best_score = GREATEST(COALESCE(best_score, 0), %s),
                    perfect = perfect OR %s
                WHERE player_id = %s AND stage_id = %s""",
                (time_s, time_s, score, perfect, player_id, stage))
            number = STAGES.index(stage)
            if number + 1 < len(STAGES):
                cur.execute("""UPDATE player_stage_progress SET status = 'UNLOCKED'
                    WHERE player_id = %s AND stage_id = %s AND status = 'LOCKED'""",
                    (player_id, STAGES[number + 1]))
        cur.execute("""UPDATE players SET character_id = COALESCE(%s, character_id),
                       last_played_at = NOW() WHERE player_id = %s""",
                    (d.get("character_id"), player_id))
        save = load_save(cur, player_id)
    return jsonify({"ok": True, "save": save})


# ---------------------------------------------------------------
# Quiz questions
# ---------------------------------------------------------------
@app.get("/questions")
def questions():
    stage = request.args.get("stage", "typhoon")
    with db() as cur:
        cur.execute("""SELECT question_id, phase, prompt, option_a, option_b, option_c, option_d
                       FROM questions WHERE stage_id = %s ORDER BY question_id""", (stage,))
        rows = [{"question_id": r[0], "phase": r[1], "prompt": r[2],
                 "options": {"A": r[3], "B": r[4], "C": r[5], "D": r[6]}}
                for r in cur.fetchall()]
    return jsonify({"ok": True, "questions": rows})


@app.post("/answer")
def answer():
    """The correct answer is checked here, so it never travels with the question."""
    player_id = current_player()
    if not player_id:
        return error("Please log in first.", 401)
    d = request.get_json(silent=True) or {}
    chosen = str(d.get("chosen", "")).upper()[:1]
    with db() as cur:
        cur.execute("SELECT correct, explanation FROM questions WHERE question_id = %s",
                    (d.get("question_id"),))
        row = cur.fetchone()
        if not row:
            return error("Unknown question.", 404)
        is_correct = chosen == row[0]
        cur.execute("""INSERT INTO answer_log (player_id, question_id, chosen, is_correct)
                       VALUES (%s, %s, %s, %s)""",
                    (player_id, d["question_id"], chosen, is_correct))
    return jsonify({"ok": True, "is_correct": is_correct,
                    "correct": row[0], "explanation": row[1]})


if __name__ == "__main__":
    # 0.0.0.0 lets the ESP32 reach it from the same Wi-Fi network.
    app.run(host="0.0.0.0", port=5000, debug=False)