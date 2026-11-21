.PHONY: run bot migrate makemigrations shell check cleanup

run:
	python3 manage.py runserver 0.0.0.0:8080

bot:
	python3 -m bot.main

migrate:
	python3 manage.py migrate

makemigrations:
	python3 manage.py makemigrations

shell:
	python3 manage.py shell

check:
	python3 manage.py check

cleanup:
	python3 manage.py server_cleanup