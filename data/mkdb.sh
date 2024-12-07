#!/bin/bash

# Create a new SQLite database
DB_NAME="database.db"

# Create the database and tables
sqlite3 "$DB_NAME" <<EOF
CREATE TABLE IF NOT EXISTS cards (
    deck_id TEXT,
    front TEXT,
    back TEXT,
    card_id TEXT
);

CREATE TABLE IF NOT EXISTS decks (
    deck_id TEXT,
    name TEXT,
    icon TEXT
);
EOF

echo "Database $DB_NAME created with tables cards and decks."
