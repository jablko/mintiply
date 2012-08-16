import base64
from mintiply import Object, object, url

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
