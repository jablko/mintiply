import base64, hashlib, os
from google.appengine.api import urlfetch

url = os.environ['PATH_INFO'][1:]
if os.environ['QUERY_STRING']:
  url += '?' + os.environ['QUERY_STRING']

result = urlfetch.fetch(url)

print 'Digest: SHA-256=' + base64.b64encode(hashlib.sha256(result.content).digest())
print 'Location: ' + url
