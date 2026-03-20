#!/bin/bash
# Deploy ke Heroku via ZIP

APP_NAME="wa-bot-reminder"
HEROKU_API_KEY="YOUR_HEROKU_API_KEY"  # Generate dari Heroku account settings

# Create ZIP
cd ai-agent
zip -r deploy.zip . -x "*.git*" "sessions/*" ".env*"

# Upload ke Heroku
curl -X POST https://api.heroku.com/apps/$APP_NAME/builds \
  -H "Authorization: Bearer $HEROKU_API_KEY" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @deploy.zip

echo "Deploy dalam progress..."
