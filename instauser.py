from google.appengine.ext import ndb


class InstaUser(ndb.Model):
    # email address of this User
    emailaddress = ndb.StringProperty();
    pro_pic = ndb.StringProperty()
    userId = ndb.StringProperty();
    userName = ndb.StringProperty();
    about = ndb.StringProperty();
    followers = ndb.StringProperty(repeated=True)
    following = ndb.StringProperty(repeated=True)
