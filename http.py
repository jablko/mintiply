import base64, os, re, urllib
from mintiply import analytics, mintiply, Object
from urlparse import urlparse, urlunparse

analytics()

# Get URL to generate Metalink for from our path info
url = os.environ['PATH_INFO'][1:]

# Handle URL without scheme
#
#   absolute-URI  = scheme ":" hier-part [ "?" query ]
#   scheme        = ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )
#
if not re.match('[A-Za-z][-A-Za-z0-9+.]*:', url):
  url = 'http://' + url

url = list(urlparse(url))
url[2] = urllib.quote(url[2])

if os.environ['QUERY_STRING']:
  url[4] = os.environ['QUERY_STRING']

url = urlunparse(url)

object = mintiply(url)

print 'Digest: SHA-256=' + base64.b64encode(object.digest)

print 'Link: </meta4/{}>; rel=describedby'.format(url)

# Add "Link: <...>; rel=duplicate" header for each URL that was already visited
# and that the digest we computed matches
for duplicate in Object.gql('WHERE digest = :1', object.digest):

  # This comparison is naive, in future we could normalize
  if duplicate.url != url:
    print 'Link: <{}>; rel=dulicate'.format(duplicate.url)

# In future we could also send 3XX status code to redirect to the URL, or to a
# preferred duplicate URL
print 'Location: ' + url
