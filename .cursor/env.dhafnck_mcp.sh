#!/bin/bash

SETTINGS_FILE=".cursor/setting.json"

if ! command -v jq &> /dev/null; then
  echo "jq is required but not installed. Please install jq (e.g., sudo apt-get install jq) and try again."
  exit 1
fi

if [ ! -f "$SETTINGS_FILE" ]; then
  echo "Settings file $SETTINGS_FILE not found."
  exit 1
fi

# Get user_id from .cursor/setting.json if it exists
user_id=$(jq -r '.user_id // empty' "$SETTINGS_FILE")
if [ -z "$user_id" ]; then
  read -p "user_id is empty. Please enter user_id: " input_user_id
  if [ -z "$input_user_id" ]; then
    echo "No user_id entered. Exiting."
    exit 1
  fi
  user_id="$input_user_id"
  # Update .cursor/setting.json with the new user_id
  tmpfile=$(mktemp)
  jq --arg uid "$user_id" '.user_id = $uid' "$SETTINGS_FILE" > "$tmpfile" && mv "$tmpfile" "$SETTINGS_FILE"
  echo "user_id updated to $user_id in $SETTINGS_FILE."
fi
  # Update .cursor/setting.json with the new user_id

# Check if project_id is empty
project_id=$(jq -r '.project_id' "$SETTINGS_FILE")
if [ -z "$project_id" ] || [ "$project_id" = "null" ]; then
  read -p "project_id is empty. Please enter project_id: " user_project_id
  if [ -z "$user_project_id" ]; then
    echo "No project_id entered. Exiting."
    exit 1
  fi
  # Update .cursor/setting.json with the new project_id
  tmpfile=$(mktemp)
  jq --arg pid "$user_project_id" '.project_id = $pid' "$SETTINGS_FILE" > "$tmpfile" && mv "$tmpfile" "$SETTINGS_FILE"
  echo "project_id updated to $user_project_id in $SETTINGS_FILE."
  project_id="$user_project_id"
fi

current_username="$(whoami)"

jq -r 'to_entries[] | "\(.key): \(.value)"' "$SETTINGS_FILE" | while IFS=: read -r key value; do
  value="${value#" "}" # trim leading space
  # Replace <username> with actual username
  value="${value//<username>/$current_username}"
  # Evaluate shell expressions like $(...)
  if [[ $value =~ ^\$\((.*)\)$ ]]; then
    eval_value=$(eval "${BASH_REMATCH[1]}")
    value="$eval_value"
  fi
  echo "$key: $value"
done