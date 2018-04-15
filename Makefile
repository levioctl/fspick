install:
	sudo pip install -U -r requirements.txt
	sudo pip install . -U

check_convention:
	pep8 fspick

clean:
	rm -rf AUTHORS build ChangeLog *.egg-info
