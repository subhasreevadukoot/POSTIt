from google.appengine.ext import ndb
from comments import Comments

class Post(ndb.Model):
    userId=ndb.StringProperty(indexed=True)
    createdDt=ndb.DateTimeProperty(auto_now_add=True)
    content=ndb.StringProperty()
    post_pic = ndb.BlobKeyProperty()
    comments=ndb.StructuredProperty(Comments, repeated=True)
