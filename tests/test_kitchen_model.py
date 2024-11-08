from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    clear_meals,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats,

)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
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

######################################################
#
#    Add and delete
#
######################################################

def test_create_meal(mock_cursor):
    """Test creating a new meal in the meal table."""

    # Call the function to create a new meal
    create_meal(meal="chicken alfredo", cuisine="american", price=17.99, difficulty="LOW")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("chicken alfredo", "american", 17.99, "LOW")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."



def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate name."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Meal with name 'chicken alfredo' already exists"):
        create_meal(meal="chicken alfredo", cuisine="american", price=17.99, difficulty="LOW")

def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an invalid price (e.g., negative price)"""

    # Attempt to create a meal with a negative price
    with pytest.raises(ValueError, match="Invalid price: -18.99. Price must be a positive number."):
        create_meal(meal="chicken alfredo", cuisine="american", price=-18.99, difficulty="LOW")

    with pytest.raises(ValueError, match="Invalid price: ten. Price must be a positive number."):
        create_meal(meal="chicken alfredo", cuisine="american", price="ten", difficulty="LOW")


def test_create_meal_invalid_difficulty():
    """Test error when trying to create a meal with an invalid difficulty (e.g., not "LOW", "MED", or "HIGH")"""

    # Attempt to create a song with a negative duration
    with pytest.raises(ValueError, match="Invalid difficulty level: BEGINNER. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="chicken alfredo", cuisine="american", price=17.99, difficulty="BEGINNER")




def test_clear_meals(mock_cursor, mocker):
    """Test deleting all meals from the meals table"""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_meal_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_database function
    clear_meals()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_meal_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()

def test_delete_meal(mock_cursor):
    """Test soft deleting a meal from the catalog by meal ID."""

    # Simulate that the song exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_song function
    delete_meal(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."

def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has been deleted"):
        delete_meal(999)

######################################################
#
#    Get Meal
#
######################################################

def test_get_meal_by_id(mock_cursor):
    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "chicken alfredo", "american", 17.99, "LOW", False)

    # Call the function and check the result
    result = get_meal_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "chicken alfredo", "american", 17.99, "LOW")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_id_bad_id(mock_cursor):
    # Simulate that no meal exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_id_already_deleted(mock_cursor):
    # Simulate that meal has already been deleted
    mock_cursor.fetchone.return_value = (1, "sallys fkass bread", "sallean", 18.00, "HIGH", True)

    # Expect a ValueError when the meal has been deleted
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        get_meal_by_id(1)

def test_get_meal_by_name(mock_cursor):
    # Simulate that the meal exists (meal = "chicken alfredo")
    mock_cursor.fetchone.return_value = (1, "chicken alfredo", "american", 17.99, "LOW", False)

    # Call the function and check the result
    result = get_meal_by_name("chicken alfredo")

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "chicken alfredo", "american", 17.99, "LOW")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("chicken alfredo",)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_bad_name(mock_cursor):
    # Simulate that no meal exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with name salad not found"):
        get_meal_by_name("salad")

def test_get_meal_by_name_already_deleted(mock_cursor):
    # Simulate that no meal exists for the given ID
    mock_cursor.fetchone.return_value = (1, "sallys fckass bread", "sllean", 18.00, "HIGH", True)

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with name sallys fckass bread has been deleted"):
        get_meal_by_name("sallys fckass bread")

def test_update_meal_stats_win(mock_cursor):
    """Test updating the stats of a meal."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with a sample meal ID and a win
    meal_id = 1
    update_meal_stats(meal_id, "win")

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_update_meal_stats_loss(mock_cursor):
    
    """Test updating the stats of a meal."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with a sample meal ID and a win
    meal_id = 1
    stat = "loss"
    update_meal_stats(meal_id, stat)

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id, )
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_update_meal_stats_invalid_stat(mock_cursor):
    """Test updating the stats of a meal to neither win or loss."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with a sample meal ID and a win

    mock_cursor.fetchone.return_value = (1, "potato", "irish", 1.00, "MED", True)
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, "WIN")

def test_update_meal_stats_already_deleted(mock_cursor):
    """Test updating the stats of a meal to neither win or loss."""

    # Call the update_meal_stats function with a sample meal ID and a win
    meal_id = "id"
    with pytest.raises(ValueError, match="Meal with ID id not found"):
        update_meal_stats(meal_id, "Win")

def test_update_meal_stats_invalid_id(mock_cursor):
    """Test updating the stats of a meal to neither win or loss."""

    # Call the update_meal_stats function with a sample meal ID and a win
    meal_id = "id"
    with pytest.raises(ValueError, match="Meal with ID id not found"):
        update_meal_stats(meal_id, "Win")

def test_get_leaderboard_by_win(mock_cursor):
    """Test retrieving leaderboard by wins."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (2, "meal B", "cuisine B", 17.99, "LOW", 50, 25, 0.5),
        (3, "meal C", "cuisine C", 17.99, "LOW", 50, 15, 0.3),
        (1, "meal A", "cuisine A", 17.99, "LOW", 50, 10, 0.2)
        
    ]

    # Call get_leaderboard
    meals = get_leaderboard()

    # Ensure the results are sorted by wins
    expected_result = [
        {"id": 2, "meal": "meal B", "cuisine": "cuisine B", "price": 17.99, "difficulty": "LOW", "battles": 50, "wins": 25, "win_pct": 50.0},
        {"id": 3, "meal": "meal C", "cuisine": "cuisine C", "price": 17.99, "difficulty": "LOW", "battles": 50, "wins": 15, "win_pct": 30.0},
        {"id": 1, "meal": "meal A", "cuisine": "cuisine A", "price": 17.99, "difficulty": "LOW", "battles": 50, "wins": 10, "win_pct": 20.0}
    ]

    assert meals == expected_result, f"Expected {expected_result}, but got {meals}"

    # Ensure the SQL query was executed correctly
    expected_quer3y = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0
        ORDER BY wins DESC
  
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_by_win_pct(mock_cursor):
    """Test retrieving leaderboard by win_pct."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (2, "meal B", "cuisine B", 17.99, "LOW", 50, 25, 0.5),
        (3, "meal C", "cuisine C", 17.99, "LOW", 50, 15, 0.3),
        (1, "meal A", "cuisine A", 17.99, "LOW", 50, 10, 0.2)
        
    ]

    # Call get_leaderboard
    meals = get_leaderboard("win_pct")

    # Ensure the results are sorted by wins
    expected_result = [
        {"id": 2, "meal": "meal B", "cuisine": "cuisine B", "price": 17.99, "difficulty": "LOW", "battles": 50, "wins": 25, "win_pct": 50.0},
        {"id": 3, "meal": "meal C", "cuisine": "cuisine C", "price": 17.99, "difficulty": "LOW", "battles": 50, "wins": 15, "win_pct": 30.0},
        {"id": 1, "meal": "meal A", "cuisine": "cuisine A", "price": 17.99, "difficulty": "LOW", "battles": 50, "wins": 10, "win_pct": 20.0}
    ]

    assert meals == expected_result, f"Expected {expected_result}, but got {meals}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0
        ORDER BY win_pct DESC
  
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    
def test_get_leaderboard_by_invalid(mock_cursor):
    """Test retrieving leaderboard with an invalid sort_by arg."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (2, "meal B", "cuisine B", 17.99, "LOW", 50, 25, 0.5),
        (3, "meal C", "cuisine C", 17.99, "LOW", 50, 15, 0.3),
        (1, "meal A", "cuisine A", 17.99, "LOW", 50, 10, 0.2)
        
    ]

    # Call get_leaderboard
    with pytest.raises(ValueError, match="Invalid sort_by parameter: price"):
        get_leaderboard("price")
