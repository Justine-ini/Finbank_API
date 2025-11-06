#!/bin/bash

set -o errexit # Exit if any error

set -o nounset # Treats unset variable as error and exit immediately

set -o pipefail # Exit with non zero status if any command in pipeline fails

FLOWER_CMD="celery \
    -A backend.app.core.celery_app \
    -b ${CELERY_BROKER_URL} \
    flower \
    --address=0.0.0.0 \
    --port=5555 \
    --basic_auth=${CELERY_FLOWER_USER}:${CELERY_FLOWER_PASSWORD}"

exec watchfiles \
    --filter python \
    --ignore-paths '.venv,.git,__pycache__,*.pyc' \
    "${FLOWER_CMD}"