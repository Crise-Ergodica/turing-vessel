#!/usr/bin/env bash
# Script to build the Turing Vessel project directory structure

set -euo pipefail

echo "Initializing directory structure..."

# Create the directories
directories=(
  "src/domain"
  "src/application"
  "src/infrastructure"
  "src/interfaces/cli"
  "tests/acceptance"
  "data/pgdata"
)

for dir in "${directories[@]}"; do
  if [ ! -d "$dir" ]; then
    mkdir -p "$dir"
    echo "Created directory: $dir"
  else
    echo "Directory already exists: $dir"
  fi
done

# Create python package init files
touch src/__init__.py
touch src/domain/__init__.py
touch src/application/__init__.py
touch src/infrastructure/__init__.py
touch src/interfaces/__init__.py
touch src/interfaces/cli/__init__.py
touch tests/__init__.py
touch tests/acceptance/__init__.py

# Add a default pytest.ini if not exists
if [ ! -f "pytest.ini" ]; then
  cat << 'EOF' > pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
pythonpath = .
EOF
  echo "Created pytest.ini"
fi

echo "Directory structure initialized successfully."
