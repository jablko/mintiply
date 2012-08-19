import hashlib, re, sys, urllib
from google.appengine.api import urlfetch
from google.appengine.ext import db
from os import path
from urlparse import urlparse

# Datastore model about a URL that was already visited.  Currently just URL and
# digest
class Object(db.Model):
  digest = db.ByteStringProperty()
  name = db.StringProperty()
  size = db.IntegerProperty()
  url = db.LinkProperty()

# content-disposition = "Content-Disposition" ":"
#                        disposition-type *( ";" disposition-parm )
# disposition-type    = "inline" | "attachment" | disp-ext-type
#                     ; case-insensitive
# disp-ext-type       = token
# disposition-parm    = filename-parm | disp-ext-parm
# filename-parm       = "filename" "=" value
#                     | "filename*" "=" ext-value
# disp-ext-parm       = token "=" value
#                     | ext-token "=" ext-value
# ext-token           = <the characters in token, followed by "*">

token = '[-!#-\'*+.\dA-Z^-z|~]+'
qdtext='[]-~\t !#-[]'
mimeCharset='[-!#-&+\dA-Z^-z]+'
valueChars = '(?:%[\dA-F][\dA-F]|[-!#$&+.\dA-Z^-z|~])*'
dispositionParm = '[Ff][Ii][Ll][Ee][Nn][Aa][Mm][Ee]\s*=\s*(?:({token})|"((?:{qdtext}|\\\\[\t !-~])*)")|[Ff][Ii][Ll][Ee][Nn][Aa][Mm][Ee]\*\s*=\s*({mimeCharset})\'[-\dA-Za-z]*\'({valueChars})|{token}\s*=\s*(?:{token}|"(?:{qdtext}|\\\\[\t !-~])*")|{token}\*\s*=\s*{mimeCharset}\'[-\dA-Za-z]*\'{valueChars}'.format(**locals())

def mintiply(url):

  # Check Datastore if the URL was already visited.  Currently we only visit a
  # URL once, and forever remember the metadata, which assumes that the content
  # at the URL never changes.  This is true for many downloads, but in future we
  # could respect cache control headers
  try:
    object, = Object.gql('WHERE url = :1', url)

  # URL not found in Datastore, download the content, compute digest, and add to
  # Datastore
  except ValueError:

    result = urlfetch.fetch(url,
      allow_truncated=True,
      deadline=sys.maxint,

      # http://code.google.com/p/googleappengine/issues/detail?id=5686
      headers={ 'Range': 'bytes=0-' + str(2 ** 25 - 1) })

    try:

      # [ disposition-type ";" ] disposition-parm ( ";" disposition-parm )* / disposition-type
      m = re.match('(?:{token}\s*;\s*)?(?:{dispositionParm})(?:\s*;\s*(?:{dispositionParm}))*|{token}'.format(**locals()), result.headers['Content-Disposition'])

    except KeyError:
      name = path.basename(urllib.unquote(urlparse(url).path))

    else:
      if not m:
        name = path.basename(urllib.unquote(urlparse(url).path))

      # Many user agent implementations predating this specification do not
      # understand the "filename*" parameter.  Therefore, when both "filename"
      # and "filename*" are present in a single header field value, recipients
      # SHOULD pick "filename*" and ignore "filename"

      elif m.group(8) is not None:
        name = urllib.unquote(m.group(8)).decode(m.group(7))

      elif m.group(4) is not None:
        name = urllib.unquote(m.group(4)).decode(m.group(3))

      elif m.group(6) is not None:
        name = re.sub('\\\\(.)', '\1', m.group(6))

      elif m.group(5) is not None:
        name = m.group(5)

      elif m.group(2) is not None:
        name = re.sub('\\\\(.)', '\1', m.group(2))

      else:
        name = m.group(1)

      # Recipients MUST NOT be able to write into any location other than one to
      # which they are specifically entitled

      if name:
        name = path.basename(name)

      else:
        name = path.basename(urllib.unquote(urlparse(url).path))

    m = hashlib.sha256()
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
    object = Object(digest=m.digest(), name=name, size=firstBytePos, url=url)
    object.put()

  return object
