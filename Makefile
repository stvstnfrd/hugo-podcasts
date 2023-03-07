GIT=git
HUGO=hugo
HUGO_FLAGS=--buildDrafts --cacheDir=$(PWD)/tmp/cache
HUGO_SITE_NAME=src
HUGO_CONFIG_FILE=$(HUGO_SITE_NAME)/config.yaml
PYTHON=PYTHONPATH=./lib ./.venv/bin/python
PYTHON_REQUIREMENTS=./lib/requirements.txt
PYLINT=PYTHONPATH=./lib ./.venv/bin/pylint

OPML_FILE=etc/feed.opml

.PHONY: help
help:  ## This.
	@perl -ne 'print if /^[a-zA-Z.-]+:.*## .*$$/' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: _virtualenv
_virtualenv:  ## Create a new virtualenv and install packages
	test -d ./.venv || python3 -m venv ./.venv
	./.venv/bin/pip install -r "$(PYTHON_REQUIREMENTS)"

.PHONY: serve
serve:  ## Serve up a preview instance of the site
	cd "$(HUGO_SITE_NAME)" && \
		"$(HUGO)" server $(HUGO_FLAGS)

.PHONY: build
build:  ## Build the Hugo site
	cd "$(HUGO_SITE_NAME)" && \
		"$(HUGO)" $(HUGO_FLAGS)

init:  ## Initialize an empty repository
	"$(HUGO)" new site "$(HUGO_SITE_NAME)"
	echo "podcasts: {}" >> "$(HUGO_CONFIG_FILE)"
	mkdir -p dist/content
	mkdir -p dist/static


GIT_IS_ACTIVE=$(shell "$(GIT)" rev-parse HEAD 2>/dev/null >/dev/null && echo 1 || echo 0)
GIT_HAS_ORIGIN=$(shell "$(GIT)" remote get-url origin 2>/dev/null >/dev/null && echo 1 || echo 0)
GIT_CAN_AUTHOR=$(shell "$(GIT)" config user.email 2>/dev/null >/dev/null && echo 1 || echo 0)
ifndef GIT_BRANCH_CONTENT
GIT_BRANCH_CONTENT=main
endif
ifndef GIT_BRANCH_STATIC
GIT_BRANCH_STATIC=$(GIT_BRANCH_CONTENT)
endif

.PHONY: update-content
update-content:  ## Update content/metadata for feeds
ifeq (1,$(GIT_IS_ACTIVE))
	@if ! $(GIT) diff --cached --exit-code . 2>/dev/null >/dev/null; then \
		$(GIT) diff --cached; \
		echo "Canceling; local changes staged for commit."; \
		exit 1; \
	fi
	"$(GIT)" status --untracked-files=all --porcelain dist/content \
	| grep '.' --silent \
	&& { \
		$(GIT) status --untracked-files=all dist/content; \
		echo "Canceling; local changes to commit."; \
	} \
	|| true
	$(GIT) branch | grep " $(GIT_BRANCH_CONTENT)$$" --silent \
	|| $(GIT) branch "$(GIT_BRANCH_CONTENT)" "main"
	"$(GIT)" checkout "$(GIT_BRANCH_CONTENT)"
ifeq (1,$(GIT_HAS_ORIGIN))
	"$(GIT)" fetch origin
	"$(GIT)" rebase "origin/$(GIT_BRANCH_CONTENT)"
endif
endif
	$(PYTHON) bin/parse-opml.py "$(OPML_FILE)" dist --content-directory content/content
	$(PYTHON) bin/parse-feed.py ./dist \
		--skip-images \
		--skip-media \
		--content-directory content/content \
		--static-directory static/static \
	;
ifeq (1,$(GIT_CAN_AUTHOR))
	"$(GIT)" status --untracked-files=all --porcelain dist/content \
	| grep '.' --silent \
	&& { \
		$(GIT) add dist/content \
		&& $(GIT) commit -m 'feat: update content' \
	; } \
	|| true
ifeq (1,$(GIT_HAS_ORIGIN))
	$(GIT) push origin "$(GIT_BRANCH_CONTENT)" \
	|| true
endif
endif

.PHONY: update-static
update-static:  ## Fetch static assets (images/audio/video)
ifeq (1,$(GIT_IS_ACTIVE))
	@if ! $(GIT) diff --cached --exit-code . 2>/dev/null >/dev/null; then \
		$(GIT) diff --cached; \
		echo "Canceling; local changes staged for commit."; \
		exit 1; \
	fi
	"$(GIT)" status --untracked-files=all --porcelain dist/static \
	| grep '.' --silent \
	&& { \
		$(GIT) status --untracked-files=all dist/static; \
		echo "Canceling; local changes to commit."; \
	} \
	|| true
ifeq (1,$(GIT_CAN_AUTHOR))
	$(GIT) branch | grep " $(GIT_BRANCH_STATIC)$$" --silent \
	|| $(GIT) branch "$(GIT_BRANCH_STATIC)" "$(GIT_BRANCH_CONTENT)"
	"$(GIT)" checkout "$(GIT_BRANCH_STATIC)"
ifeq (1,$(GIT_HAS_ORIGIN))
	"$(GIT)" fetch origin
	"$(GIT)" rebase "origin/$(GIT_BRANCH_STATIC)"
endif
	"$(GIT)" merge --no-ff -m 'feat: pull in content changes' "$(GIT_BRANCH_CONTENT)"
endif
endif
	$(PYTHON) bin/parse-opml.py "$(OPML_FILE)" dist --content-directory content/content
	$(PYTHON) bin/parse-feed.py ./dist \
		--content-directory content/content \
		--static-directory static/static \
	;
ifeq (1,$(GIT_CAN_AUTHOR))
	"$(GIT)" status --untracked-files=all --porcelain dist/static \
	| grep '.' --silent \
	&& { \
		$(GIT) add dist/static \
		&& $(GIT) commit -m 'feat: update static' \
	; } \
	|| true
ifeq (1,$(GIT_HAS_ORIGIN))
	"$(GIT)" status --untracked-files=all --porcelain dist/static \
	| grep '.' --silent \
	&& { \
		$(GIT) push origin "$(GIT_BRANCH_STATIC)" \
	; } \
	|| true
endif
endif
