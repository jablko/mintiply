import os, re, unicodedata, urllib
from mintiply import analytics, mintiply, Object, token
from urlparse import urlparse, urlunparse

analytics()

# Get URL to generate Metalink for from our path info
url = os.environ['PATH_INFO'][7:]

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

m = re.match('[\t !-~]*$', object.name)
if m:
  filename = object.name
  extParameter = ''

else:

  # The normal form KD (NFKD) will apply the compatibility decomposition, i.e.
  # replace all compatibility characters with their equivalents

  # What I *really* want is "iconv -t ASCII//TRANSLIT", why was the iconv module
  # dropped from Python 2.3?

  filename = unicodedata.normalize('NFKD', object.name).encode('ascii', 'ignore')
  extParameter = '; filename*=utf-8\'\'{}.meta4'.format(urllib.quote(object.name.encode('utf-8'), '!#$&+^`|~'))

m = re.match(token + '$', filename)
if m:
  filename += '.meta4'

else:
  filename = '"{}.meta4"'.format(filename.replace('"', '\\"'))

print 'Content-Disposition: filename={}{}'.format(filename, extParameter)

print 'Content-Type: application/metalink4+xml'

print

print '<metalink xmlns="urn:ietf:params:xml:ns:metalink">'
print '  <file name="{}">'.format(object.name.replace('<', '&lt;').replace('&', '&amp;').replace('"', '&quot;').encode('utf-8'))

print '    <hash type="sha-256">{}</hash>'.format(object.digest.encode('hex'))
print '    <size>{}</size>'.format(object.size)

# Add <url/> element for each URL that was already visited and that the digest
# we computed matches
for duplicate in Object.gql('WHERE digest = :1', object.digest):
  print '    <url>{}</url>'.format(duplicate.url.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

print '  </file>'
print '</metalink>'
