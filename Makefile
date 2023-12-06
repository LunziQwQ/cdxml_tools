.PHONY: build test

install:
	@pip install --no-cache-dir -r requirements.txt
	@python setup.py install
	@make clean

test:
	@python -m unittest discover -v -p *_test.py 

clean:
	@rm -r build || true
	@rm -r dist || true
	@rm -r *.egg-info || true
	@find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
