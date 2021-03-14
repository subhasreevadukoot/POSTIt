from google.appengine.ext import ndb
#model for comments
class Comments(ndb.Model):
    userId=ndb.StringProperty(indexed=True)
    content=ndb.StringProperty()
    #date and time of comment creation
    createdDt=ndb.DateTimeProperty(auto_now_add=True)
