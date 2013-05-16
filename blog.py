import jinja2
import os
import webapp2

from google.appengine.api import users
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

# Takes parameters to fill in the jinja template.
class TemplateHandler(webapp2.RequestHandler):
  def write_response(self, *a, **kw):
    self.response.out.write(*a, **kw)

  def render_template(self, template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

  def send_response(self, template, **kw):
    self.write_response(self.render_template(template, **kw))

class Post(db.Model):
  subject = db.StringProperty(required = True)
  content = db.TextProperty(required = True)
  created = db.DateTimeProperty(auto_now_add = True)
  owner = db.StringProperty(required = False)
  last_modified = db.DateTimeProperty(auto_now = True)

  def render(self):
    self._render_text = self.content.replace('\n', '<br>')
    t = jinja_env.get_template("post.html")
    return t.render(p = self)

class BlogFront(TemplateHandler):
  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
    posts = db.GqlQuery("select * from Post order by created desc limit 10")
    self.send_response('front.html', posts = posts)

# For displaying a single post.
class SinglePostPage(TemplateHandler):
  def get(self, post_id):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))

    key = db.Key.from_path('Post', int(post_id))
    post = db.get(key)

    if not post:
      self.error(404)
      return

    self.send_response("permalink.html", post = post)

# For new post.
class NewPostPage(TemplateHandler):
  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
    self.send_response("newpost.html")
  
  def post(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
    subject = self.request.get('subject')
    content = self.request.get('content')
    
    if subject and content:
      p = Post(subject = subject, content = content, owner = user.nickname())
      p.put()
      self.redirect('/blog/%s' % str(p.key().id()))
    else:
      error = "Fill in both subject and content, please!"
      self.send_response("newpost.html", subject=subject,
                         content=content, error=error)

app = webapp2.WSGIApplication([('/', BlogFront),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', SinglePostPage),
                               ('/blog/newpost', NewPostPage),
                               ],
                              debug=True)
