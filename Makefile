extract:
	pybabel extract -F babel.cfg -o messages.pot .
init:
	pybabel init -i messages.pot -d locales -l ru  # повторить для всех языков
update:
	pybabel update -i messages.pot -d locales
compile:
	pybabel compile -d locales
