SRC=./tf_strategy
TEST_SRC=./tests

TO_FORMAT=$(SRC) $(OCTO_SRC) $(TEST_SRC)

format:
	ruff check --fix $(TO_FORMAT)
	black $(TO_FORMAT)

lint:
	ruff check $(TO_FORMAT)
	black --check $(TO_FORMAT)