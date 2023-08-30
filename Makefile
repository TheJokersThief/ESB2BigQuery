.PHONY: test coverage lint docs clean dev install help export_conf create_pubsub_topic deploy_to_gfunctions

PROJECT_NAME = esb2bigquery
PROJECT_ID ?= example-project
SCHEDULE ?= "0 8 * * *"

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

ensure-poetry:
	@if ! [ -x $(command -v poetry) ]; then \
		echo "Please install poetry (e.g. pip install poetry)"; \
		exit 1; \
	fi

lint: ensure-poetry  ## Lint files for common errors and styling fixes
	poetry check
	poetry run flake8 --ignore F821,W504 $(project)

clean:
	find . -name '*.pyc' -delete
	find . -name __pycache__ -delete
	rm -rf .coverage dist build htmlcov *.egg-info

dev: ensure-poetry clean  ## Install project and dev dependencies
	poetry install

install: ensure-poetry clean  ## Install project without dev dependencies
	poetry install --no-dev

export_conf:  ## Export the poetry lockfile to requirements.txt
	poetry export -f requirements.txt --output requirements.txt --without-hashes

create_pubsub_topic:
ifeq ($(shell gcloud --project=${PROJECT_ID} pubsub topics list --filter="name~trigger-${PROJECT_NAME}" | wc -l), 0)
	gcloud --project=${PROJECT_ID} pubsub topics create "trigger-${PROJECT_NAME}"
endif

deploy_to_gfunctions: create_pubsub_topic export_conf
	gcloud functions deploy ${PROJECT_NAME} \
		--gen2 \
		--region europe-west1 \
		--project ${PROJECT_ID} \
		--runtime python39 \
		--memory 128Mi \
		--entry-point loadToBigQuery \
		--trigger-topic "trigger-${PROJECT_NAME}" \
		--set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID},TOPIC_NAME=trigger-${PROJECT_NAME} \
		--set-secrets 'ESB_MPRN=esb_mprn:latest,ESB_USERNAME=esb_username:latest,ESB_PASSWORD=esb_password:latest,ESB_BIGQUERY_DB=esb_bigquery_db:latest'\
		--timeout 60s \
		--max-instances 1

publish: deploy_to_gfunctions  ## Publish project to google cloud functions
	@echo "Published"

add_job:  ## Adds a message to the pubsub topic, using the content in misc/scheduled-payload.json
	gcloud pubsub topics publish "projects/${PROJECT_ID}/topics/trigger-${PROJECT_NAME}" --message='$(shell cat misc/scheduled-payload.json)'

add_schedule:  ## Adds a Cloud Scheduler job to periodically run the job data collection
	gcloud scheduler jobs create pubsub --project ${PROJECT_ID} ${PROJECT_NAME} \
		--schedule ${SCHEDULE} \
		--topic "trigger-${PROJECT_NAME}" \
		--location europe-west1 \
		--time-zone "Europe/Dublin" \
		--message-body-from-file misc/scheduled-payload.json

update_schedule:  ## Updates an existing Cloud Scheduler job
	gcloud scheduler jobs update pubsub --project ${PROJECT_ID} ${PROJECT_NAME} \
		--schedule ${SCHEDULE} \
		--topic "trigger-${PROJECT_NAME}" \
		--message-body-from-file misc/scheduled-payload.json \
		--time-zone "Europe/Dublin" \
		--location europe-west1
