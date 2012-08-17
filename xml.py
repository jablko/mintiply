import binascii, urllib
from mintiply import Object, object, url
from os import path
from urlparse import urlparse

basename = path.basename(urllib.unquote(urlparse(url).path))

print 'Content-Disposition: filename="{}.meta4"'.format(basename.replace('"', '\\"'))
print 'Content-Type: application/metalink4+xml'

print

print '<metalink xmlns="urn:ietf:params:xml:ns:metalink">'
print '  <file name="{}">'.format(basename.replace('<', '&lt;').replace('&', '&amp;').replace('"', '&quot;'))

print '    <hash type="sha-256">{}</hash>'.format(binascii.hexlify(object.digest))

# Add <url/> element for each URL that was already visited and that the digest
# we computed matches
for duplicate in Object.gql('WHERE digest = :1', object.digest):
  print '    <url>{}</url>'.format(duplicate.url.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

print '  </file>'
print '</metalink>'
