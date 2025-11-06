#!/bin/bash


set -o errexit # Exit if any error

set -o nounset # Treats unset variable as error and exit immediately

set -o pipefail # Exit with non zero status if any command in pipeline fails

exec watchfiles --filter python celery.__main__.main --args '-A backend.app.core.celery_app beat -l INFO'