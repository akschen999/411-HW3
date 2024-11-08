import pytest 
import re
from contextlib import contextmanager

import sqlite3


from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal, update_meal_stats


@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

@pytest.fixture()
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()

@pytest.fixture
def mock_update_meal_stats(mocker):
    """Mock the update_play_count function for testing purposes."""
    return mocker.patch("meal_max.models.kitchen_model.update_meal_stats")

@pytest.fixture
def mock_get_random(mocker):
    '''mock the get random function for testing purposes'''
    return mocker.patch("meal_max.utils.random_utils.get_random")


"""Fixtures providing sample meals for the tests."""
@pytest.fixture
def sample_meal1():
    return Meal(1, 'potatoes', 'irish', 1.00, 'MED')

@pytest.fixture
def sample_meal2():
    return Meal(2, 'sallys fkass bread', 'salleian', 18.00, 'HIGH')

@pytest.fixture
def sample_battle(sample_meal1, sample_meal2):
    return [sample_meal1, sample_meal2]


def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()


##################################################
#Battle Test Cases
##################################################

def test_battle(battle_model,sample_meal1, sample_meal2, mock_cursor):
    mock_cursor.fetchone.return_value = ([False])
    
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    

    s1 =battle_model.get_battle_score(sample_meal1)
    s2 =battle_model.get_battle_score(sample_meal2)
    delta = abs(s1 - s2) / 100


    random_num = 0.42

    if delta > random_num:
            winner = sample_meal1
            loser = sample_meal2
    else:
            winner = sample_meal2
            loser = sample_meal1


    assert winner.meal == battle_model.battle(), "Winner between combatants Potatoes and Sally's bread should be Potatoes"

    '''
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    battle_model.battle()
    assert len(battle_model.combatants)==1, "Losing combatant should be removed from combatants list"
    '''
    
    
    
    '''
    mock_cursor.fetchone.return_value = [False]

    #battle_model.combatants.extend(sample_battle)
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    
    s1 =battle_model.get_battle_score(sample_meal1)
    s2 =battle_model.get_battle_score(sample_meal2)
    delta = abs(s1 - s2) / 100

    random_num = 0.42

    if delta > random_num:
            winner = sample_meal1
            loser = sample_meal2
    else:
            winner = sample_meal2
            loser = sample_meal1

    update_meal_stats(winner.id, 'win')
    
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?", (meal_id,)
    """)
    
    
    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."


    mock_update_meal_stats.assert_called_once_with(loser.id, 'loss')
    '''

    
def test_battle_not_enough_combatants(battle_model):
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

##################################################
# Add Combatant Management Test Cases
##################################################

def test_prep_combatant(battle_model, sample_meal1):
    """Test prepping a combatant"""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].meal == 'potatoes'

def test_prep_combatant_overfill(battle_model, sample_meal1):
    """Test error when adding a combatant to the battle where there are already two combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal1)
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(sample_meal1)



##################################################
# Clear Comba\tant Management Test Cases
##################################################


def test_clear_combatants(battle_model, sample_meal1):
    """Test clearing combatants."""
    battle_model.prep_combatant(sample_meal1)

    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0, "Combatants should be empty after clearing"


def test_get_battle_score(battle_model, sample_battle, sample_meal1):
    """Test successfully retrieving the battle score from a combatant."""
    battle_model.combatants.extend(sample_battle)

    assert battle_model.get_battle_score(sample_meal1) == 3.000, "Meal potatoes with difficulty med should have battle score 3.000"
    
def test_get_combatants(battle_model, sample_battle):
    """Test successfully retrieving all combatants from the battle."""
    battle_model.combatants.extend(sample_battle)

    all_combatants = battle_model.get_combatants()
    assert len(all_combatants) == 2
    assert all_combatants[0].id == 1
    assert all_combatants[1].id == 2
