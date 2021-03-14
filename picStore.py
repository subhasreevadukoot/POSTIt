from google.appengine.ext import ndb

#Model to store profile picture
class PicStore(ndb.Model):
    picId = ndb.StringProperty()
    pics = ndb.BlobKeyProperty()
