#!/bin/bash
# deploy.sh – Safe deployment script with rollback, date-aware log filtering, and deployment history

# === CONFIGURATION ===
DEV_DIR="./dev"
PROD_DIR="./prod"
BACKUP_DIR="./prod_backup"
LOG_FILE="./data_cleaning.log"
CHANGELOG="./changelog.txt"
PYTHON_SCRIPT="./Main.py"
STORED_VERSION_FILE=".last_deployed_version"
DEPLOYMENT_HISTORY="./deployment_history.log"

TODAY=$(date +"%Y-%m-%d")
NOW=$(date +"%Y-%m-%d %H:%M:%S")

echo "=== 🚀 Starting Deployment Process ==="

log_event() {
    # Helper function to log to deployment history
    echo "[$NOW] $1" >> "$DEPLOYMENT_HISTORY"
}

# === STEP 1: Run tests ===
echo "🧪 Running tests..."
pytest > pytest_output.log 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. See pytest_output.log for details."
    log_event "❌ Deployment FAILED — Tests did not pass."
    exit 1
fi
echo "✅ Tests passed."

# === STEP 2: Run ETL pipeline ===
echo "🔄 Running ETL pipeline..."
python "$PYTHON_SCRIPT"
if [ $? -ne 0 ]; then
    echo "❌ ETL process crashed. Check $LOG_FILE for details."
    log_event "❌ Deployment FAILED — ETL process crashed."
    exit 1
fi
echo "✅ ETL script executed."

# === STEP 3: Check today's log entries for errors ===
echo "🔎 Checking logs for today's errors ($TODAY)..."
TODAY_ERRORS=$(grep "^$TODAY" "$LOG_FILE" | grep "ERROR")

if [ -n "$TODAY_ERRORS" ]; then
    echo "❌ Errors detected during today's ETL run. Aborting deployment."
    echo "Recent errors:"
    echo "$TODAY_ERRORS"
    log_event "❌ Deployment FAILED — Errors detected in today's logs."
    exit 1
fi
echo "✅ No errors detected today."

# === STEP 4: Compare versions ===
LATEST_VERSION=$(grep -Eo "v[0-9]+\.[0-9]+" "$CHANGELOG" | tail -n 1)
if [ -f "$STORED_VERSION_FILE" ]; then
    LAST_DEPLOYED_VERSION=$(cat "$STORED_VERSION_FILE")
else
    LAST_DEPLOYED_VERSION="none"
fi

if [ "$LATEST_VERSION" == "$LAST_DEPLOYED_VERSION" ]; then
    echo "ℹ️ No new version detected (still $LATEST_VERSION). Skipping deployment."
    log_event "ℹ️ Deployment skipped — no new version (current: $LATEST_VERSION)."
    exit 0
fi

echo "📦 New version detected: $LATEST_VERSION (previous: $LAST_DEPLOYED_VERSION)"
log_event "🚀 Deployment started for version $LATEST_VERSION (previous: $LAST_DEPLOYED_VERSION)"

# === STEP 5: Backup current production files ===
mkdir -p "$BACKUP_DIR"
echo "🗄️ Creating backup of current production files..."
cp "$PROD_DIR"/*.db "$BACKUP_DIR"/ 2>/dev/null

# === STEP 6: Deploy only modified files ===
mkdir -p "$PROD_DIR"
DEPLOY_FAILED=false

for FILE in "$DEV_DIR"/*.db; do
    if [ "$LAST_DEPLOYED_VERSION" == "none" ] || [ "$FILE" -nt "$STORED_VERSION_FILE" ]; then
        echo "➡️  Deploying $(basename "$FILE")..."
        cp "$FILE" "$PROD_DIR"/ || DEPLOY_FAILED=true
    fi
done

# === STEP 7: Rollback if deployment failed ===
if [ "$DEPLOY_FAILED" = true ]; then
    echo "❌ Deployment failed. Rolling back to previous version..."
    cp "$BACKUP_DIR"/*.db "$PROD_DIR"/
    echo "🔄 Rollback complete. Production restored to previous state."
    log_event "❌ Deployment FAILED — Rolled back to previous version $LAST_DEPLOYED_VERSION."
    exit 1
fi

# === STEP 8: Save deployed version ===
echo "$LATEST_VERSION" > "$STORED_VERSION_FILE"
echo "✅ Deployment complete (version $LATEST_VERSION)."
log_event "✅ Deployment SUCCESS — Version $LATEST_VERSION deployed successfully."

echo "=== 🎉 Deployment Finished Successfully ==="
