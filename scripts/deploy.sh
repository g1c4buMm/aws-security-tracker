#!/usr/bin/env bash
# Add a week, build, and publish the AWS Security Launch Tracker.
#
#   ./scripts/deploy.sh data/weeks/w41.json            # merge + build only
#   TARGET=amplify AMPLIFY_APP_ID=d123abc AMPLIFY_BRANCH=main ./scripts/deploy.sh data/weeks/w41.json
#   TARGET=s3 S3_BUCKET=my-tracker-bucket CF_DISTRIBUTION_ID=E123ABC ./scripts/deploy.sh data/weeks/w41.json
#   TARGET=github ./scripts/deploy.sh data/weeks/w42.json   # commit + push; GitHub Actions publishes to Pages
#
# Needs: python3; for amplify/s3, AWS CLI v2 with credentials (AWS_PROFILE or SSO) and curl, zip.
set -euo pipefail
cd "$(dirname "$0")/.."

WEEK_FILE="${1:-}"
TARGET="${TARGET:-none}"

if [[ -n "$WEEK_FILE" ]]; then
  python3 scripts/add_week.py "$WEEK_FILE"
fi
python3 scripts/build.py

case "$TARGET" in
  amplify)
    : "${AMPLIFY_APP_ID:?set AMPLIFY_APP_ID}"; BRANCH="${AMPLIFY_BRANCH:-main}"
    rm -f dist/site.zip
    (cd dist && zip -q site.zip index.html)
    read -r JOB_ID UPLOAD_URL < <(aws amplify create-deployment \
      --app-id "$AMPLIFY_APP_ID" --branch-name "$BRANCH" \
      --query '[jobId, zipUploadUrl]' --output text)
    curl -sSf -X PUT -H "Content-Type: application/zip" --upload-file dist/site.zip "$UPLOAD_URL"
    aws amplify start-deployment --app-id "$AMPLIFY_APP_ID" --branch-name "$BRANCH" --job-id "$JOB_ID" \
      --query 'jobSummary.status' --output text
    echo "Amplify job $JOB_ID started for branch $BRANCH"
    ;;
  s3)
    : "${S3_BUCKET:?set S3_BUCKET}"
    aws s3 cp dist/index.html "s3://$S3_BUCKET/index.html" \
      --content-type "text/html; charset=utf-8" --cache-control "max-age=300"
    if [[ -n "${CF_DISTRIBUTION_ID:-}" ]]; then
      aws cloudfront create-invalidation --distribution-id "$CF_DISTRIBUTION_ID" --paths "/index.html" "/" \
        --query 'Invalidation.Id' --output text
    fi
    ;;
  github)
    git add data/launches.json ${WEEK_FILE:+"$WEEK_FILE"}
    if git diff --cached --quiet; then
      echo "Nothing new to commit"
    else
      W=$(python3 -c "import json;print(max(r['w'] for r in json.load(open('data/launches.json'))))")
      git commit -m "Tracker: add week $W"
      git push
      echo "Pushed. GitHub Actions builds and publishes to Pages (Actions tab shows progress)."
    fi
    ;;
  none)
    echo "Built dist/index.html (TARGET not set, nothing deployed)"
    ;;
  *) echo "Unknown TARGET=$TARGET (use github, amplify, s3 or none)"; exit 1 ;;
esac
