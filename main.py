import webapp2
import jinja2
from google.appengine.ext import ndb
from google.appengine.api import users
from instauser import InstaUser
from timeline import Timeline
from timeline import DoPosts
from timeline import UpdatePic
from timeline import SignUp
from timeline import SearchUser
from timeline import Profile
from timeline import DisplayPics
from timeline import FollowUser
from timeline import FollowList
from timeline import Comment
import os



JINJA_ENVIRONMENT=jinja2.Environment(
loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
extensions=['jinja2.ext.autoescape'],
autoescape=True
)
#class for signup and storing user info
class MainPage(webapp2.RequestHandler):
    def get(self):
        user=users.get_current_user()
        if user:
            myuser_key=ndb.Key('InstaUser',user.user_id())
            myuser=myuser_key.get()
            if myuser == None:
                template_values= {
                'id': user.user_id(),
                'emailaddress': user.email()
                }
                template= JINJA_ENVIRONMENT.get_template('signUp.html')
                self.response.write(template.render(template_values))

            else  :
                self.redirect('/timeline')
        else :
            url= users.create_login_url('/')
            url_string= 'Login'
            template_values= {
            'url': url,
            'url_string': url_string
            }
            template= JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))



#for logout functionality
class Logout(webapp2.RequestHandler):
    def get(self):
        user=users.get_current_user()
        if user :
            self.redirect(users.create_logout_url('/'))

# starts the web application we specify the full routing table here as well
app = webapp2.WSGIApplication([
    ('/',MainPage),
    ('/logout',Logout),
    ('/timeline',Timeline),
    ('/doPost',DoPosts),
    ('/profilePic',UpdatePic),
    ('/signup',SignUp),
    ('/searchUser',SearchUser),
    ('/followUser',FollowUser),
    ('/profile',Profile),
    ('/followList',FollowList),
    ('/fetchPic',DisplayPics),
    ('/doComment',Comment),

    ],debug=True)
