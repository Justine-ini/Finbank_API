#!/bin/bash


set -o errexit # Exit if any error

set -o nounset # Treats unset variable as error and exit immediately

set -o pipefail # Exit with non zero status if any command in pipeline fails


exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
