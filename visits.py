import urllib
from google.appengine.api import app_identity
from google.appengine.api import urlfetch
from time import gmtime, strftime

url = 'https://www.googleapis.com/analytics/v3/data/ga?' + urllib.urlencode((
  ('dimensions', 'ga:pagePath'),
  ('end-date', strftime('%Y-%m-%d', gmtime())),
  ('ids', 'ga:63243011'),
  ('metrics', 'ga:visits'),
  ('start-date', '2005-01-01')))

token, _ = app_identity.get_access_token('https://www.googleapis.com/auth/analytics.readonly')

result = urlfetch.fetch(url, headers={ 'Authorization': 'OAuth ' + token })

print

print result.content
