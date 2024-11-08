#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments

while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service

check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}


##########################################################
#
# Meal Management
#
##########################################################

clear_meals() {
  echo "Clearing the meals table..."
  curl -s -X DELETE "$BASE_URL/clear-meals" | grep -q '"status": "success"'
}

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Adding meal ($meal, $cuisine, $price, $difficulty) to the table..."
  curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "meal added successfully."
  else
    echo "Failed to add meal."
    exit 1
  fi
}

delete_meal_by_id() {
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully by ID ($meal_id)."
  else
    echo "Failed to delete song by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_id() {
  meal_id=$1

  echo "Getting song by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by ID ($meal_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Song JSON (ID $meal_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get song by ID ($song_id)."
    exit 1
  fi
}

get_meal_by_name() {
  name=$1
  
  echo "Getting meal by name (Name: '$name')..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-name/$name")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by name."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (by name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name."
    exit 1
  fi
}


############################################################
#
# Battle Management
#
############################################################


battle() {

response=$(curl -s -X GET "$BASE_URL/battle" \
    -H "Content-Type: application/json")
if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle successful."
    if [ "$ECHO_JSON" = true ]; then
      echo "Song JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to battle."
    exit 1
  fi

}

clear_combatants() {
    echo "Clearing combatants..."
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Playlist cleared successfully."
  else
    echo "Failed to clear playlist."
    exit 1
  fi
}

get_combatants() {
    echo "Getting all combatants in the battle..."
  response=$(curl -s -X GET "$BASE_URL/get-combatants")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "All combatants retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Songs JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get combatants."
    exit 1
  fi
}

prep_combatant() {
  meal=$1
  
  echo "Preparing meal: $meal..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant" \
  -H "Content-Type: application/json" \
  -d "{\"meal\":\"$meal\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatant $meal prepared successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON:"
      echo "$response" | jq .
    fi
  else
    
    echo "Failed to prepare combatant $meal ."
    exit 1
  fi
}


############################################################
#
# Leaderboard
#
############################################################

# Function to get the meal leaderboard sorted by wins
get_leaderboard() {
    echo "Getting meal leaderboard sorted by win percentage..."
    sort_by="wins"
  response=$(curl -s -X GET "$BASE_URL/leaderboard?sort=$sort_by")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON (sorted by win percentage):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal leaderboard."
    exit 1
  fi
}


# Health checks
check_health
check_db

# Clear the catalog
clear_meals

# Create meals
create_meal "chicken alf" "american" 17.99 "LOW" 
create_meal "shakshuka" "mediterranean" 18.20 "MED" 
create_meal "coconut curry" "thai" 10.49 "LOW" 
create_meal "udon" "japanese" 20.59 "HIGH" 
create_meal "vindaloo" "indian" 30.55 "LOW" 

# Deleting chicken alf
delete_meal_by_id 1

# Testing get meals
get_meal_by_name "udon"
get_meal_by_id 4


clear_combatants
prep_combatant "udon" 
prep_combatant "vindaloo" 
battle

get_combatants

get_leaderboard



