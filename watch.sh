#!/bin/bash

BACKEND_IMAGE="htsago/backend-llm:latest"
FRONTEND_IMAGE="htsago/frontend-llm:latest"

BACKEND_PATH="./"
FRONTEND_PATH="./chat"

BACKEND_DOCKERFILE="Dockerfile.fastapi"
FRONTEND_DOCKERFILE="chat/Dockerfile"

echo "🚀 Watching for changes..."
echo "Backend: $BACKEND_IMAGE (Dockerfile: $BACKEND_DOCKERFILE)"
echo "Frontend: $FRONTEND_IMAGE (Dockerfile: $FRONTEND_DOCKERFILE)"

while true; do
  CHANGED=$(inotifywait -r -e modify,create,delete,move --format '%w%f' $BACKEND_PATH $FRONTEND_PATH)

  if [[ $CHANGED == $BACKEND_PATH* ]]; then
    echo "🛠️  Änderung im Backend erkannt: $CHANGED"
    docker build -t $BACKEND_IMAGE -f $BACKEND_DOCKERFILE $BACKEND_PATH
    if [ $? -eq 0 ]; then
      echo "✅ Backend Build erfolgreich. Push läuft..."
      docker push $BACKEND_IMAGE
    else
      echo "❌ Backend Build fehlgeschlagen."
    fi
  elif [[ $CHANGED == $FRONTEND_PATH* ]]; then
    echo "🛠️  Änderung im Frontend erkannt: $CHANGED"
    docker build -t $FRONTEND_IMAGE -f $FRONTEND_DOCKERFILE $FRONTEND_PATH
    if [ $? -eq 0 ]; then
      echo "✅ Frontend Build erfolgreich. Push läuft..."
      docker push $FRONTEND_IMAGE
    else
      echo "❌ Frontend Build fehlgeschlagen."
    fi
  fi

  echo "⏳ Beobachte weiter..."
done
