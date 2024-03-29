COVERAGE=$(PYTHON_LIB) $(PYTHON_VENV_BIN)/coverage
COVERAGE_XML=$(TMP)/coverage.xml
PYLINT=$(PYTHON_LIB) $(PYTHON_VENV_BIN)/pylint
PYLINT_FLAGS=--disable fixme
XMLLINT=xmllint
XMLLINT_FLAGS=--noout

.PHONY: lint
test: lint-make lint-xml lint-hugo lint-python test-python  ## Run the entire suite: short for `make lint-make lint-xml lint-hugo lint-python test-python`

.PHONY: lint-python
lint-python: _lint-python-requirements  ### Lint python code for consistency
	$(PYLINT) $(PYTHON_LIB_PATH) $(PYLINT_FLAGS)

.PHONY: lint-python-todo
lint-python-todo: _lint-python-requirements  ### Check for TODO items in Python files
	$(PYLINT) $(PYTHON_LIB_PATH) --disable all --enable fixme

.PHONY: _lint-python-requirements
_lint-python-requirements: requirements-python  ## Install requirements for Python linting
	$(PIP_INSTALL) pylint

.PHONY:
test-python: _test-python-requirements  ### Check that the python test suite passes
	$(COVERAGE) run -m unittest discover "$(PYTHON_LIB_PATH)"
	test -d "$(TMP)" || mkdir -p "$(TMP)"
	$(COVERAGE) xml -o '$(COVERAGE_XML)'
	$(COVERAGE) report

.PHONY: _test-python-requirements
_test-python-requirements: requirements-python  ### Install requirements for Python testing
	$(PIP_INSTALL) coverage

.PHONY: lint-xml
lint-xml: requirements-system  ### Check that the OPML file is valid
	# TODO: install requirements
	$(XMLLINT) $(XMLLINT_FLAGS) "$(OPML_FILE)"

.PHONY: lint-hugo
lint-hugo:  ### Check that the Hugo documents build
	$(MAKE) build

.PHONY: lint-make
lint-make:  ### Check that the Makefile is valid
	$(MAKE) help
