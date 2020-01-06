run:
	pipenv run dbq
.PHONY: run

develop:
	pipenv install --dev
.PHONY: develop

lint:
	pipenv run flake8
	pipenv run black --diff -l 80 -S dbq
.PHONY: lint

format:
	pipenv run black -l 80 -S dbq
.PHONY: format

dist:
	rm -f dist/*
	pipenv run python setup.py sdist bdist_wheel
.PHONY: dist

publish: dist
	pipenv run twine upload dist/*
.PHONY: publish
