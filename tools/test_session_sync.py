import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.core.session import GameSession
from src.core.database import db_manager

def test_session_db_sync():
    session = GameSession()
    session.challenger_name = "SessionTester"
    session.character = {"id": "juan", "name": "Juan"}
    session.complete_stage("earthquake")
    
    print("Session completed stages:", session.completed)
    print("Session unlocked stages:", session.unlocked)
    
    # Check DB
    p_id = session.db_player_id
    assert p_id, "Session should have db_player_id"
    prog = db_manager.load_player_progress(p_id)
    print("DB Progress after complete_stage:", prog)
    assert "earthquake" in prog["completed"], "earthquake should be marked completed in DB"
    assert "landslide" in prog["unlocked"], "landslide should be unlocked in DB"

    print("SUCCESS: Session DB sync works perfectly!")

if __name__ == "__main__":
    test_session_db_sync()
