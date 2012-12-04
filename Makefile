all:
	@echo "See Makefile for options."

run:
	@echo "Launching app..."
	dev_appserver.py app

deploy:
	# Remember to increment the version number in app.yaml
	@echo "Deploying app..."
	appcfg.py --oauth2 update app
