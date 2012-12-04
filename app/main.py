import webapp2
import jinja2
import os
import sys

packages_path = os.path.join(os.path.dirname(__file__), "vendor")
sys.path.insert(0, packages_path)

import httplib2

from google.appengine.api import users
from apiclient.discovery import build
from oauth2client.appengine import oauth2decorator_from_clientsecrets
from oauth2client.client import AccessTokenRefreshError
from google.appengine.api import memcache

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'config/client_secrets.json')
MISSING_CLIENT_SECRETS_MESSAGE = "Please configure the OAuth 2.0 file found at: %s" % CLIENT_SECRETS

http = httplib2.Http(memcache)
service = build("latitude", "v1", http=http)
decorator = oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/latitude.current.best',
    message=MISSING_CLIENT_SECRETS_MESSAGE)


class MainHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))


class StepOneHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        template_values = {
            'name': user.nickname(),
            'logout': users.create_logout_url('/')}
        template = jinja_environment.get_template('step1.html')
        self.response.out.write(template.render(template_values))


class StepTwoHandler(webapp2.RequestHandler):
    @decorator.oauth_aware
    def get(self):
        template_values = {
            'authorize_url': decorator.authorize_url(),
            'has_credentials': decorator.has_credentials()}
        template = jinja_environment.get_template('step2.html')
        self.response.out.write(template.render(template_values))


class DataHandler(webapp2.RequestHandler):
    @decorator.oauth_required
    def get(self):
        try:
            http = decorator.http()
            location = service.currentLocation().get(granularity='best').execute(http=http)
            template_values = {
                'kind': location.get('kind', '-'),
                'timestampMs': location.get('timestampMs', '-'),
                'latitude': location.get('latitude', '-'),
                'longitude': location.get('longitude', '-'),
                'accuracy': location.get('accuracy', '-'),
                'speed': location.get('speed', '-'),
                'heading': location.get('heading', '-'),
                'altitude': location.get('altitude', '-'),
                'altitudeAccuracy': location.get('altitudeAccuracy', '-'),
                'activityId': location.get('activityId', '-')}
            template = jinja_environment.get_template('data.html')
            self.response.out.write(template.render(template_values))
        except AccessTokenRefreshError:
            self.redirect('/')

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/step1', StepOneHandler),
    ('/step2', StepTwoHandler),
    ('/data', DataHandler),
    (decorator.callback_path, decorator.callback_handler())
], debug=True)
