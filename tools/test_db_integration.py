import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.core.database import db_manager

def test_db_operations():
    print("Testing DB connection...")
    assert db_manager.is_connected, "DB should be connected"

    print("Testing get_or_create_player...")
    player = db_manager.get_or_create_player("TestPlayer", character_id="juan")
    print("Player created/retrieved:", player)
    assert player and player["player_id"] > 0, "Player ID must be valid"
    p_id = player["player_id"]

    print("Testing update_player_character...")
    updated = db_manager.update_player_character(p_id, "maria")
    assert updated, "Character update should succeed"

    print("Testing record_stage_run...")
    run_ok = db_manager.record_stage_run(
        player_id=p_id,
        stage_id="home_island_tutorial",
        time_seconds=45,
        score=950,
        completed=True,
        perfect=True,
        damage_taken=0,
        objectives_done=3,
        items_found=2,
        next_stage_id="earthquake"
    )
    assert run_ok, "Stage run record should succeed"

    print("Testing load_player_progress...")
    progress = db_manager.load_player_progress(p_id)
    print("Loaded progress:", progress)
    assert "home_island_tutorial" in progress["completed"], "home_island_tutorial should be completed"
    assert "earthquake" in progress["unlocked"], "earthquake should be unlocked"
    assert progress["records"]["home_island_tutorial"]["best_score"] == 950

    print("Testing high scores...")
    scores = db_manager.get_high_scores("home_island_tutorial")
    print("Top scores:", scores)
    assert len(scores) > 0, "Should have high score records"

    print("Testing quiz questions...")
    q = db_manager.get_questions("typhoon")
    print(f"Retrieved {len(q)} questions for typhoon")
    assert len(q) > 0, "Should have quiz questions"

    print("Testing answer logging...")
    ans_ok = db_manager.log_answer(p_id, q[0]["question_id"], "A", True)
    assert ans_ok, "Answer logging should succeed"

    print("ALL DB OPERATIONS TESTED AND PASSED 100%!")

if __name__ == "__main__":
    test_db_operations()
