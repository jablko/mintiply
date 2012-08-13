import base64, hashlib, os, sys
from google.appengine.api import urlfetch
from google.appengine.ext import db

# Datastore model about a URL that was already visited.  Currently just URL and
# digest
class Object(db.Model):
  digest = db.ByteStringProperty()
  url = db.LinkProperty()

# Get URL to generate Metalink for from our path info
url = os.environ['PATH_INFO'][1:]
if os.environ['QUERY_STRING']:
  url += '?' + os.environ['QUERY_STRING']

# Check Datastore if the URL was already visited.  Currently we only visit a
# URL once, and forever remember the metadata, which assumes that the URL never
# changes.  This is true for many downloads, but in future we could respect
# cache control headers
try:
  object, = Object.gql('WHERE url = :1', url)

# URL not found in Datastore, download the content, compute digest, and add to
# Datastore
except ValueError:
  m = hashlib.sha256()

  result = urlfetch.fetch(url,
    allow_truncated=True,
    deadline=sys.maxint,

    # http://code.google.com/p/googleappengine/issues/detail?id=5686
    headers={ 'Range': 'bytes=0-' + str(2 ** 25 - 1) })

  m.update(result.content)

  # Use byte ranges to overcome App Engine maximum response size.  Because
  # allow_truncated is broken (App Engine issue 5686) and because
  # Content-Length is broken on some servers (e.g. they report message length
  # vs. entity length), continue downloading if:
  #
  #   * content_was_truncated, or
  #   * we so far downloaded less than Content-Length, or
  #   * the last segment was as large as the byte range that was requested,
  #     suggesting that there is still more data, regardless of Content-Length
  #
  firstBytePos = len(result.content)
  while result.content_was_truncated or firstBytePos < int(result.headers['Content-Length']) or len(result.content) > 2 ** 25 - 1:

    result = urlfetch.fetch(url,
      allow_truncated=True,
      deadline=sys.maxint,

      # http://code.google.com/p/googleappengine/issues/detail?id=5686
      headers={ 'Range': 'bytes={}-{}'.format(firstBytePos, firstBytePos + 2 ** 25 - 1) })

    m.update(result.content)

    firstBytePos += len(result.content)

  # Add URL to Datastore
  object = Object(digest=m.digest(), url=url)
  object.put()

# Generate Metalink

print 'Digest: SHA-256=' + base64.b64encode(object.digest)

# Add "Link: <...>; rel=duplicate" header for each URL that was already visited
# and that the digest we computed matches
for duplicate in Object.gql('WHERE digest = :1', object.digest):

  # This comparison is naive, in future we could normalize
  if duplicate.url != url:
    print 'Link: <{}>; rel=dulicate'.format(duplicate.url)

# In future we could also send 3XX status code to redirect to the URL, or to a
# preferred duplicate URL
print 'Location: ' + url
