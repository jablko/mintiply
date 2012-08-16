import binascii
from mintiply import Object, object

print 'Content-Type: application/metalink4+xml'

print

print '<metalink xmlns="urn:ietf:params:xml:ns:metalink">'
print '  <file>'

print '    <hash type="sha-256">{}</hash>'.format(binascii.hexlify(object.digest))

# Add <url/> element for each URL that was already visited and that the digest
# we computed matches
for duplicate in Object.gql('WHERE digest = :1', object.digest):
  print '    <url>{}</url>'.format(duplicate.url)

print '  </file>'
print '</metalink>'
