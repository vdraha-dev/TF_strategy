SRC=./src

TO_FORMAT=$(SRC) $(OCTO_SRC)

format:
	ruff check --fix $(TO_FORMAT)
	black $(TO_FORMAT)

lint:
	ruff check $(TO_FORMAT)
	black --check $(TO_FORMAT)