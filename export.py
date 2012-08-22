from mintiply import analytics, Object

analytics()

print 'Content-Type: application/metalink4+xml'

print

print '<metalink xmlns="urn:ietf:params:xml:ns:metalink">'

for object in Object.all():
  print '  <file name="{}">'.format(object.name.replace('<', '&lt;').replace('&', '&amp;').replace('"', '&quot;').encode('utf-8'))
  print '    <hash type="sha-256">{}</hash>'.format(object.digest.encode('hex'))
  print '    <size>{}</size>'.format(object.size)
  print '    <url>{}</url>'.format(object.url.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
  print '  </file>'

print '</metalink>'
