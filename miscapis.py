import wsgiref.handlers, urllib2, logging
from google.appengine.ext import webapp
from google.appengine.api import memcache

class Form(webapp.RequestHandler):
  def get(self):
    self.response.out.write("""\
<!DOCTYPE html>
<title>MiscAPIs</title>
<h2>xpandurl</h2>
<form action=/xpandurl target=_blank><pre>
      URL: <input name=url title=u(rl) size=80 value=http://goo.gl/mR2d>
 callback: <input name=callback title=c(allback) size=20
><input type=submit></pre></form>
<h2>webiconv</h2>
<form action=/webiconv target=_blank><pre>
      URL: <input name=url  title=u(rl)  size=80>
  charset: <input name=from title=f(rom) size=16
   > -&gt; <input name=to   title=t(o)   size=16 value=euc-jp
><input type=submit></pre></form>
""")

class XpandURL(webapp.RequestHandler):
  def get(self, path):
    rq, rs = self.request, self.response
    url = rq.get('u') or rq.get('url') or urllib2.unquote(path)
    cb  = rq.get('c') or rq.get('callback')
    loc = memcache.get(url, 'xpu')
    if not loc:
      req = urllib2.Request(url, headers = rq.headers)
      req.get_method = lambda: 'HEAD'
      res = None
      try:
        res = urllib2.urlopen(req)
      except urllib2.HTTPError, ex:
        logging.error('%s %s\n%s' % (ex.code, ex.msg, ex.read()))
        rs.set_status(ex.code, ex.msg)
      except urllib2.URLError, ex:
        logging.error(ex)
        rs.set_status(500, `ex`)
      if res:
        loc = res.geturl().decode('utf-8')
        memcache.set(url, loc, time = 180, namespace = 'xpu')
      else:
        loc = url
    if cb:
      import pprint
      loc = cb +'("'+ (pprint.pformat("'"+ loc.replace('"', '\0'))
                       .replace(r'\x00', r'\"')[3:]) +')'
    rs.headers.add_header('Content-Type', 'text/plain;charset=utf-8')
    rs.out.write(loc)

class WebIConv(webapp.RequestHandler):
  def get(self):
    rq, rs = self.request, self.response
    url = rq.get('u') or rq.get('url') or 'http://google.com'
    csf = rq.get('f') or rq.get('from')
    cst = rq.get('t') or rq.get('to') or 'utf-8'
    res = urllib2.urlopen(url)
    head = res.info()
    tipe, cso = detype(head)
    rs.headers.add_header('Content-Type', tipe, charset = str(cst))
    rs.out.write(iconv(res.read(), csf or cso, cst))

class Cr0n(webapp.RequestHandler):
  def get(self, path):
    rs = self.response
    if not path: return
    try:
      url = urllib2.unquote(path)
      res = urllib2.urlopen(url)
    except Exception, ex:
      logging.error(ex)
      return
    head = res.info()
    rs.headers.add_header('Content-Type', 'text/plain;charset=utf-8')
    rs.out.write(str(head) +'\n')
    text = iconv(res.read(), detype(head)[1])
    rs.out.write(text)
    logging.info(text)

def detype(head):
  ct = head['content-type'] or 'text/plain'
  return (str(ct.split(';', 1)[0].strip()),
          str(ct.rsplit('=', 1)[-1].strip() if ct.count('=') else ''))

def iconv(s, fr = '', to = ''):
  if s[0:3] == '\xef\xbb\xbf': s = s[3:] # nuking BOM
  if fr: s = s.decode(fr)
  return s.encode(to or 'utf-8')

def main():
  wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
    (r'/', Form),
    (r'/(?:web)?iconv(?:site)?/?', WebIConv),
    (r'/e?xp(?:and)?u(?:rl)?/?(.*)', XpandURL),
    (r'/cr0n/?(.*)', Cr0n),
    ], debug=True))

if __name__ == '__main__': main()
