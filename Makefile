
clean:
	rm -rf build dist venv

init:
	python3 -m venv venv
	@./venv/bin/python3 -m pip install -U pip setuptools
	@./venv/bin/python3 -m pip install -r requirements.txt -U

