# ────────────────────────────────────────────────────────────────────────────
# DOCKER LOCAL
# ────────────────────────────────────────────────────────────────────────────
DOCKER_NAME     := hexagonal_architecture
CONTAINER_NAME  := $(shell echo "$(PROJECT_NAME)" | tr '[:upper:]' '[:lower:]' | tr -s ' _-' '-' | sed 's/-*$$//; s/^-*//')
REPO_URL        := $(shell git remote get-url origin 2>/dev/null)
REGISTRY_URL  := $(shell echo "$(REPO_URL)" | \
                    sed -e 's|https://gitlab\.com/|https://hub.docker.com/|' \
                        -e 's|\.git$$||' | tr '[:upper:]' '[:lower:]')
REGISTRY_PATH := $(shell echo "$(REGISTRY_URL)" | sed 's|https://||')
ifeq ($(strip $(VERSION)),)
VERSION     := v$(shell grep '^version[[:space:]]*=' pyproject.toml | head -n 1 | sed 's/version[[:space:]]*=[[:space:]]*"\(.*\)"/\1/')
endif

.PHONY: docker-tags
docker-tags: ## Show the currents docker tags
	@echo "$(ARROW) Building Docker image for arm64..."
	@echo "   Registry : $(INFO)$(REGISTRY_PATH)$(NO_COLOR)"
	@echo "   Version  : $(INFO)$(VERSION)$(NO_COLOR)"

.PHONY: check-docker
check-docker: ## Verify Docker is available
	@docker --version >/dev/null 2>&1 || { echo "❌ Docker not found at docker"; exit 1; }

.PHONY: docker-build
docker-build: ## Build Docker image
	@docker build -f Dockerfile \
		--secret id=artifactory_user,env=UV_INDEX_GITLAB_USERNAME --secret id=artifactory_password,env=UV_INDEX_GITLAB_PASSWORD \
		-t $(REGISTRY_PATH):$(VERSION) -t $(REGISTRY_PATH):latest --no-cache --load . \
		&& echo "$(ARROW) Building image... done"

.PHONY: docker-build-all
docker-build-all: ## Build all Docker images
	@cd apps && cd agent && @$(MAKE) docker-build
	@cd apps && cd api && @$(MAKE) docker-build
	@cd apps && cd mcp && @$(MAKE) docker-build


.PHONY: docker-run
docker-run:  ## Run container locally (port 5000)
	@echo "$(ARROW) Starting container $(INFO)$(CONTAINER_NAME)$(NO_COLOR)..."
	@-docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@-docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@docker run -d --name $(CONTAINER_NAME) -p 5000:5000 $(REGISTRY_PATH):$(VERSION)
	@echo "$(OK) Container running → http://localhost:5000"

.PHONY: docker-stop
docker-stop:  ## Stop and remove container
	@echo "$(ARROW) Stopping container $(INFO)$(CONTAINER_NAME)$(NO_COLOR)..."
	@-docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@-#docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@echo "$(OK) Container stopped and removed"

.PHONY: docker-rm
docker-rm:  ## Remove container
	@echo "$(ARROW) Removing container $(INFO)$(DOCKER_NAME)$(NO_COLOR)..."
	@docker rm $(REGISTRY_PATH):$(VERSION) 2>/dev/null || true
	@echo "$(OK) Container removed and removed"

.PHONY: docker-logs
docker-logs:  ## Show container logs
	@echo "$(ARROW) Showing logs for $(INFO)$(CONTAINER_NAME)$(NO_COLOR)..."
	@docker logs -f $(CONTAINER_NAME)

.PHONY: docker-push
docker-push:  ## Push Docker image to registry
	@echo "$(ARROW) Pushing images to registry..."
	@docker push $(REGISTRY_PATH):$(VERSION)
	@docker push $(REGISTRY_PATH):latest
	@echo "$(OK) Images pushed"

.PHONY: docker-all
docker-all: docker-build docker-run docker-logs ## Execute build run and logs together
