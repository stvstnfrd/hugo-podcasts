GIT=git
GIT_THEME=https://github.com/frjo/hugo-theme-zen.git
GIT_THEME_DIR=$(HUGO_SITE_NAME)/themes/zen
HUGO=hugo
HUGO_FLAGS=--buildDrafts --cacheDir=$(PWD)/tmp/cache
HUGO_SITE_NAME=src
HUGO_CONFIG_FILE=$(HUGO_SITE_NAME)/config.yaml
PYTHON=PYTHONPATH=./lib ./.venv/bin/python
PYTHON_REQUIREMENTS=./lib/requirements.txt
PYLINT=PYTHONPATH=./lib ./.venv/bin/pylint
COVERAGE=PYTHONPATH=./lib ./.venv/bin/coverage

OPML_FILE=etc/feed.opml

.PHONY: virtualenv
virtualenv:
	test -d ./.venv || python3 -m venv ./.venv
	./.venv/bin/pip install -r "$(PYTHON_REQUIREMENTS)"

.PHONY: serve
serve:
	cd "$(HUGO_SITE_NAME)" && \
		"$(HUGO)" server $(HUGO_FLAGS)

.PHONY: build
build:
	cd "$(HUGO_SITE_NAME)" && \
		"$(HUGO)" $(HUGO_FLAGS)

init:
	"$(HUGO)" new site "$(HUGO_SITE_NAME)"
	"$(GIT)" submodule add "$(GIT_THEME)" "$(GIT_THEME_DIR)"
	echo "theme: \"zen\"" >> "$(HUGO_CONFIG_FILE)"
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

.PHONY: update-theme
update-theme:
	@if ! $(GIT) diff --cached --exit-code . 2>/dev/null >/dev/null; then \
		$(GIT) diff --cached; \
		echo "Canceling; local changes staged for commit."; \
		exit 1; \
	fi
	@if ! $(GIT) diff --exit-code src/go.mod src/go.sum 2>/dev/null >/dev/null; then \
		$(GIT) diff src/go.mod src/go.sum; \
		echo "Canceling; local changes to commit."; \
		exit 1; \
	fi
	cd "$(HUGO_SITE_NAME)" && \
		"$(HUGO)" mod get -u github.com/frjo/hugo-theme-zen \
		&& "$(HUGO)" mod tidy;
ifeq (1,$(GIT_IS_ACTIVE))
	$(GIT) add src/go.mod src/go.sum
	$(GIT) commit -m 'chore: bump theme versions' || true
else
	echo "$(GIT_IS_ACTIVE)"
endif

.PHONY: update-content
update-content:
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
update-static:
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
	$(GIT) branch | grep " $(GIT_BRANCH_STATIC)$$" --silent \
	|| $(GIT) branch "$(GIT_BRANCH_STATIC)" "$(GIT_BRANCH_CONTENT)"
	"$(GIT)" checkout "$(GIT_BRANCH_STATIC)"
ifeq (1,$(GIT_HAS_ORIGIN))
	"$(GIT)" fetch origin
	"$(GIT)" rebase "origin/$(GIT_BRANCH_STATIC)"
endif
	"$(GIT)" merge --no-ff -m 'feat: pull in content changes' "$(GIT_BRANCH_CONTENT)"
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

.PHONY: lint-python
lint-python:
	$(PYLINT) lib/ --disable fixme

.PHONY: lint-todo
lint-todo:
	$(PYLINT) lib/ --disable all --enable fixme

.PHONY: lint-hugo
lint-hugo:
	$(MAKE) build

.PHONY:
test-python:
	$(COVERAGE) run -m unittest discover lib/
	$(COVERAGE) report
