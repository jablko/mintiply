import hashlib, os, re, sys, urllib
from google.appengine.api import urlfetch
from google.appengine.ext import db
from os import path
from random import random
from time import gmtime, strftime, time
from urlparse import urlparse

# Datastore model about a URL that was already visited.  Currently just URL and
# digest
class Object(db.Model):
  digest = db.ByteStringProperty()
  name = db.StringProperty()
  size = db.IntegerProperty()
  url = db.LinkProperty()

cookieOctet = '[!#-+\\--:<-[\\]-~]'
token = '[!#-\'*+\\-.\dA-Z^-z|~]+'
qdtext='[\t !#-[\\]-~]'
mimeCharset='[!#-&+\\-\dA-Z^-z]+'
valueChars = '(?:%[\dA-F][\dA-F]|[!#$&+\\-.\dA-Z^-z|~])*'

def mintiply(url):

  # cookie-header = "Cookie:" OWS cookie-string OWS
  # cookie-string = cookie-pair *( ";" SP cookie-pair )

  cookiePair = '__utmmobile\s*=\s*(?:({cookieOctet}*)|"({cookieOctet}*)")|{token}\s*=\s*(?:{cookieOctet}*|"{cookieOctet}*")'.format(cookieOctet=cookieOctet, token=token)

  try:
    match = re.match('(?:{cookiePair})(?:\s*;\s*(?:{cookiePair}))*'.format(cookiePair=cookiePair), os.environ['HTTP_COOKIE'])

  except KeyError:
    try:
      utmvid = '0x' + hashlib.md5(os.environ['HTTP_USER_AGENT'] + str(random())).hexdigest()[:16]

    except KeyError:
      utmvid = '0x' + hashlib.md5(str(random())).hexdigest()[:16]

  else:
    if match:
      if match.group(4) is not None:
        utmvid = match.group(4)

      elif match.group(3) is not None:
        utmvid = match.group(3)

      elif match.group(2) is not None:
        utmvid = match.group(2)

      else:
        utmvid = match.group(1)

      if not utmvid:
        try:
          utmvid = '0x' + hashlib.md5(os.environ['HTTP_USER_AGENT'] + str(random())).hexdigest()[:16]

        except KeyError:
          utmvid = '0x' + hashlib.md5(str(random())).hexdigest()[:16]

    else:
      try:
        utmvid = '0x' + hashlib.md5(os.environ['HTTP_USER_AGENT'] + str(random())).hexdigest()[:16]

      except KeyError:
        utmvid = '0x' + hashlib.md5(str(random())).hexdigest()[:16]

  # Always try and add the cookie to the response
  print 'Set-Cookie: __utmmobile={}; Expires={}; Path=/'.format(utmvid, strftime('%a, %d %b %Y %T GMT', gmtime(time() + 60 * 60 * 24 * 365 * 2)))

  params = [
    ('utmac', 'MO-9761239-2'),
    ('utmcc', '__utma%3D999.999.999.999.999.1%3B'),
    ('utmhn', os.environ['SERVER_NAME']),
    ('utmn', random()),
    ('utmp', os.environ['PATH_INFO']),
    ('utmvid', utmvid),
    ('utmwv', '4.4sh')]

  match = re.match('\d+\.\d+\.\d+\.', os.environ['REMOTE_ADDR'])
  if match:
    params.append(('utmip', match.group(0) + '0'))

  try:
    params.append(('utmr', os.environ['HTTP_REFERER']))

  except KeyError:
    pass

  utmUrl = 'http://www.google-analytics.com/__utm.gif?' + urllib.urlencode(params)

  headers = {}

  try:
    headers['Accept-Language'] = os.environ['HTTP_ACCEPT_LANGUAGE']

  except KeyError:
    pass

  try:
    headers['User-Agent'] = os.environ['HTTP_USER_AGENT']

  except KeyError:
    pass

  urlfetch.fetch(utmUrl, headers=headers)

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
      headers={ 'Range': 'bytes=0-' + str(2 ** 24 - 1) })

    digest = hashlib.sha256()
    digest.update(result.content)

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

    dispositionParm = '[Ff][Ii][Ll][Ee][Nn][Aa][Mm][Ee]\s*=\s*(?:({token})|"((?:{qdtext}|\\\\[\t !-~])*)")|[Ff][Ii][Ll][Ee][Nn][Aa][Mm][Ee]\*\s*=\s*({mimeCharset})\'[-\dA-Za-z]*\'({valueChars})|{token}\s*=\s*(?:{token}|"(?:{qdtext}|\\\\[\t !-~])*")|{token}\*\s*=\s*{mimeCharset}\'[-\dA-Za-z]*\'{valueChars}'.format(token=token, qdtext=qdtext, mimeCharset=mimeCharset, valueChars=valueChars)

    try:

      # [ disposition-type ";" ] disposition-parm ( ";" disposition-parm )* / disposition-type
      match = re.match('(?:{token}\s*;\s*)?(?:{dispositionParm})(?:\s*;\s*(?:{dispositionParm}))*|{token}'.format(token=token,  dispositionParm=dispositionParm), result.headers['Content-Disposition'])

    except KeyError:
      name = path.basename(urllib.unquote(urlparse(url).path))

    else:
      if match:

        # Many user agent implementations predating this specification do not
        # understand the "filename*" parameter.  Therefore, when both
        # "filename" and "filename*" are present in a single header field
        # value, recipients SHOULD pick "filename*" and ignore "filename"

        if match.group(8) is not None:
          name = urllib.unquote(match.group(8)).decode(match.group(7))

        elif match.group(4) is not None:
          name = urllib.unquote(match.group(4)).decode(match.group(3))

        elif match.group(6) is not None:
          name = re.sub('\\\\(.)', '\1', match.group(6))

        elif match.group(5) is not None:
          name = match.group(5)

        elif match.group(2) is not None:
          name = re.sub('\\\\(.)', '\1', match.group(2))

        else:
          name = match.group(1)

        # Recipients MUST NOT be able to write into any location other than one
        # to which they are specifically entitled

        if name:
          name = path.basename(name)

        else:
          name = path.basename(urllib.unquote(urlparse(url).path))

      else:
        name = path.basename(urllib.unquote(urlparse(url).path))

    # Use byte ranges to overcome App Engine maximum response size
    firstBytePos = len(result.content)

    try:

      # Content-Range           = byte-content-range-spec
      #                         / other-content-range-spec
      # byte-content-range-spec = bytes-unit SP
      #                           byte-range-resp-spec "/"
      #                           ( instance-length / "*" )
      # byte-range-resp-spec    = (first-byte-pos "-" last-byte-pos)
      #                         / "*"
      # instance-length         = 1*DIGIT
      # other-content-range-spec = other-range-unit SP
      #                            other-range-resp-spec
      # other-range-resp-spec    = *CHAR

      match = re.match('[Bb][Yy][Tt][Ee][Ss]\s*\d+\s*-\s*\d+\s*/\s*(\d+)', result.headers['Content-Range'])

    except KeyError:
      pass

    else:
      if match:
        while result.content_was_truncated or firstBytePos < int(match.group(1)):

          result = urlfetch.fetch(url,
            allow_truncated=True,
            deadline=sys.maxint,

            # http://code.google.com/p/googleappengine/issues/detail?id=5686
            headers={ 'Range': 'bytes={}-{}'.format(firstBytePos, firstBytePos + 2 ** 24 - 1) })

          digest.update(result.content)

          firstBytePos += len(result.content)

    # Add URL to Datastore
    object = Object(digest=digest.digest(), name=name, size=firstBytePos, url=url)
    object.put()

  return object
