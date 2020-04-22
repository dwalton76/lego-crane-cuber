
clean:
	rm -rf build dist venv

init:
	python3 -m venv venv
	@./venv/bin/python3 -m pip install -U pip setuptools
	@./venv/bin/python3 -m pip install wheel setuptools python-daemon opencv-python
	@./venv/bin/python3 -m pip install git+https://github.com/dwalton76/rubiks-color-resolver.git
	@./venv/bin/python3 -m pip install git+https://github.com/dwalton76/rubiks-cube-tracker.git


