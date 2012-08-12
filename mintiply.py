import base64, hashlib, os, sys
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
    allow_truncated=True,
    deadline=sys.maxint,

    # http://code.google.com/p/googleappengine/issues/detail?id=5686
    headers={ 'Range': 'bytes=0-' + str(2 ** 25 - 1) })

  m.update(result.content)

  firstBytePos = len(result.content)
  while result.content_was_truncated or firstBytePos < int(result.headers['Content-Length']) or len(result.content) > 2 ** 25 - 1:

    result = urlfetch.fetch(url,
      allow_truncated=True,
      deadline=sys.maxint,

      # http://code.google.com/p/googleappengine/issues/detail?id=5686
      headers={ 'Range': 'bytes={}-{}'.format(firstBytePos, firstBytePos + 2 ** 25 - 1) })

    m.update(result.content)

    firstBytePos += len(result.content)

  object = Object(digest=m.digest(), url=url)
  object.put()

print 'Digest: SHA-256=' + base64.b64encode(object.digest)
print 'Location: ' + url
