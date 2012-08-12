import base64, hashlib, os
from google.appengine.api import urlfetch
from google.appengine.ext import db

class Object(db.Model):
  digest = db.ByteStringProperty()
  url = db.LinkProperty()

url = os.environ['PATH_INFO'][1:]
if os.environ['QUERY_STRING']:
  url += '?' + os.environ['QUERY_STRING']

try:
  object, = Object.gql('WHERE url = :1', url)

except ValueError:
  m = hashlib.sha256()

  result = urlfetch.fetch(url,
    allow_truncated=True)

  m.update(result.content)

  firstBytePos = len(result.content)
  while result.content_was_truncated:
    result = urlfetch.fetch(url,
      allow_truncated=True,
      headers={ 'Range': 'bytes={}-'.format(firstBytePos) })

    m.update(result.content)

    firstBytePos += len(result.content)

  object = Object(digest=m.digest(), url=url)
  object.put()

print 'Digest: SHA-256=' + base64.b64encode(object.digest)
print 'Location: ' + url
