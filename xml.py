import re, unicodedata, urllib
from mintiply import Object, object, token, url

# The normal form KD (NFKD) will apply the compatibility decomposition, i.e.
# replace all compatibility characters with their equivalents

# What I *really* want is "iconv -t ASCII//TRANSLIT", why was the iconv module
# dropped from Python 2.3?

filename = unicodedata.normalize('NFKD', object.name).encode('ascii', 'ignore') + '.meta4'

m = re.match(token + '$', filename)
if not m:
  filename = '"{}"'.format(filename.replace('"', '\\"'))

print 'Content-Disposition: filename={}; filename*=utf-8\'\'{}.meta4'.format(filename, urllib.quote(object.name.encode('utf-8'), '!#$&+^`|~'))

print 'Content-Type: application/metalink4+xml'

print

print '<metalink xmlns="urn:ietf:params:xml:ns:metalink">'
print '  <file name="{}">'.format(object.name.replace('<', '&lt;').replace('&', '&amp;').replace('"', '&quot;').encode('utf-8'))

print '    <hash type="sha-256">{}</hash>'.format(object.digest.encode('hex'))

# Add <url/> element for each URL that was already visited and that the digest
# we computed matches
for duplicate in Object.gql('WHERE digest = :1', object.digest):
  print '    <url>{}</url>'.format(duplicate.url.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

print '  </file>'
print '</metalink>'
