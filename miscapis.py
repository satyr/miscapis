import wsgiref.handlers
from google.appengine.ext import webapp

class Form(webapp.RequestHandler):
  def get(self):
    self.response.out.write("""\
<!doctype html>
<title>MiscAPIs</title>
<h2>xpandurl</h2>
<form action=/xpandurl target=_blank><pre>
      URL: <input name=url size=80>
 callback: <input name=callback size=20
><input type=submit></pre></form>
<h2>webiconv</h2>
<form action=/webiconv target=_blank><pre>
      URL: <input name=url size=80>
  charset: <input name=from size=16> -&gt; <input name=to size=16
><input type=submit></pre></form>
""")

class XpandURL(webapp.RequestHandler):
  def get(self, path):
    import urllib2, logging
    myreq = self.request
    url = myreq.get('url') or urllib2.unquote(path)
    cb  = myreq.get('callback', None)
    req = urllib2.Request(url, headers = myreq.headers)
    req.get_method = lambda: 'HEAD'
    res = None
    try:
      res = urllib2.urlopen(req)
    except urllib2.HTTPError, ex:
      logging.error('%s %s\n%s' % (ex.code, ex.msg, ex.read()))
      res = ex
    except urllib2.URLError, ex:
      logging.error(ex)
      myres.set_status(500, `ex`)
    loc = res.geturl().decode('utf-8') if res else url
    if cb != None:
      import pprint
      loc = cb +'("'+ (pprint.pformat("'"+ loc.replace('"', '\0'))
                       .replace(r'\x00', r'\"')[3:]) +')'
    myres = self.response
    myres.headers.add_header('Content-Type', 'text/plain;charset=utf-8')
    myres.out.write(loc)

class WebIConv(webapp.RequestHandler):
  def get(self):
    import urllib2
    url = self.request.get('url', 'http://miscapis.appspot.com')
    csf = self.request.get('from', '')
    cst = self.request.get('to', '')
    res = urllib2.urlopen(url)
    head = res.info()
    mime = str((head['content-type'] or 'text/html') +'; charset='+ cst)
    self.response.headers.add_header('Content-Type', mime)
    self.response.out.write(iconv(res.read(), csf, cst))

class Cr0n(webapp.RequestHandler):
  def get(self, path):
    if(not path): return
    import urllib2, logging
    try:
      url = urllib2.unquote(path)
      res = urllib2.urlopen(url)
    except Exception, ex:
      logging.error(str(ex))
      return
    head = res.info()
    cset = 'utf-8'
    mmsp = head['content-type'].split('=')
    if len(mmsp) == 2: cset = mmsp.pop()
    self.response.headers.add_header('Content-Type',
                                     'text/plain;charset=utf-8')
    self.response.out.write(str(head) +'\n')
    text = iconv(res.read(), cset)
    self.response.out.write(text)
    logging.info(text)

def iconv(s, fr, to):
  if s[0:3] == '\xef\xbb\xbf': s = s[3:] # nuking BOM
  return s.decode(fr or 'utf-8').encode(to or 'utf-8')

def main():
  wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
    (r'/', Form),
    (r'/(?:web)?iconv(?:site)?/?', WebIConv),
    (r'/e?xp(?:and)?u(?:rl)?/?(.*)', XpandURL),
    (r'/cr0n/?(.*)', Cr0n),
    ], debug=True))

if __name__ == '__main__': main()
