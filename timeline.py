import webapp2
import jinja2
import mimetypes
import os
from google.appengine.api import users
from google.appengine.ext import ndb
from posts import Post
from instauser import InstaUser
from comments import Comments
from picStore import PicStore
import datetime
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

JINJA_ENVIRONMENT = jinja2.Environment(
loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
extensions=['jinja2.ext.autoescape'],
autoescape=True
)


class Timeline(webapp2.RequestHandler):#Renders timeline for logined user
    def get(self):
        user=users.get_current_user()
        data = getUserInfo(user)
        self.response.headers['Content-Type'] = 'text/html'
        all_post = getTimeLine(data['user'].key.id()) # fetching timeline posts
        template_values = {
         'insta_user': data['user'],
         'all_posts':all_post,
         'all_user_search':all_users(user.email()),
         'post_pic_url' : blobstore.create_upload_url('/doPost')

        }
        template = JINJA_ENVIRONMENT.get_template('Timeline.html')
        self.response.write(template.render(template_values))

class Profile(webapp2.RequestHandler): #Renders profile page of all users
    def get(self):
        user=users.get_current_user()
        instauser_key=ndb.Key('InstaUser',user.user_id())
        instauser=instauser_key.get()
        id = self.request.get('id')
        data = getUserKeyData(id) # fetches user data
        self.response.headers['Content-Type'] = 'text/html'
        all_post = getAllPostsUser(id) # fetches all profile posts

        if id !=user.user_id() :
            template_values = {
             'insta_user':data,
             'all_posts':all_post,
             'owner_user':instauser,
             'all_user_search':all_users(user.email()),
            }
        else:
            template_values = {
             'insta_user':data,
             'all_posts':all_post,
             'pro_pic_url' : blobstore.create_upload_url('/profilePic'),
             'all_user_search':all_users(user.email()),
            }

        template = JINJA_ENVIRONMENT.get_template('Profile.html')
        self.response.write(template.render(template_values))

class UpdatePic(blobstore_handlers.BlobstoreUploadHandler): # update profile picture
    def get(self):
        user=users.get_current_user()
        instauser_key=ndb.Key('InstaUser',user.user_id())
        instauser=instauser_key.get()
        self.response.headers['Content-Type'] = 'text/html'
        template_values = {
         'users':user,
         'pro_pic':instauser,
         'pro_pic_url' : blobstore.create_upload_url('/profilePic'),
         'all_user_search':all_users(user.email()),
        }
        template = JINJA_ENVIRONMENT.get_template('Profile.html')
        self.response.write(template.render(template_values))
    def post(self):
        user=users.get_current_user()
        instauser_key=ndb.Key('InstaUser',user.user_id())
        instauser=instauser_key.get()
        profilePic = None
        if self.get_uploads() :
            profilePic = self.get_uploads()[0]
            picInfo = blobstore.BlobInfo(profilePic.key())
            picName = picInfo.filename

        if profilePic :
            picStore_results = PicStore.query(PicStore.picId==instauser.key.id()).fetch()

            if picStore_results :
                picStore_key = picStore_results[0]
                picStore_key.pics = profilePic.key()
            else :
                picStore_key = PicStore()
                picStore_key.picId = instauser.key.id()
                picStore_key.pics = profilePic.key()
            picStore_key.put()
            instauser.pro_pic = picName
            instauser.put()

        self.redirect('/profile?id='+instauser.key.id())

#BlobstoreDownloadHandler is used for displaying images of posts
class DisplayPics(blobstore_handlers.BlobstoreDownloadHandler):  # fetches image from blobstore
        def get(self):
            mode = self.request.get('mode')
            picId = (self.request.get('id'))
            if mode=='PROFILE':
                picStore_results = PicStore.query(PicStore.picId==picId).fetch()
                if picStore_results:
                    picStore_key = picStore_results[0]
                    self.send_blob(picStore_key.pics)
            elif mode=='POST' :
                post_key=ndb.Key('Post',int(self.request.get('id')))
                post=post_key.get()
                self.send_blob(post.post_pic)
#BlobstoreUploadHandler is used for  images in post
class DoPosts(blobstore_handlers.BlobstoreUploadHandler): # creates posts
    def post(self):
        postPic = None
        user=users.get_current_user()
        data = getUserInfo(user)
        data['all_posts'] = getTimeLine(data['user'].key.id()) #fetched timeline posts
        postid = Post.allocate_ids(1000)[0]
        newPost = Post(id=postid)
        newPost.userId = data['user'].key.id()
        newPost.createdDt=datetime.datetime.utcnow()+datetime.timedelta(hours=1)
        newPost.content=self.request.get('content')
        #Using  blobstore functionality
        if self.get_uploads() :
            postPic = self.get_uploads()[0]
            picInfo = blobstore.BlobInfo(postPic.key())
            picName = picInfo.filename

        if postPic :
            newPost.post_pic = postPic.key()

        newPost.put()
        self.response.headers['Content-Type'] = 'text/html'
        data['all_posts'].insert(0, postToList(newPost))
        data['insta_user'] = data['user']
        data['all_user_search'] = all_users(user.email())
        data['post_pic_url'] = blobstore.create_upload_url('/doPost')
        template = JINJA_ENVIRONMENT.get_template('Timeline.html')
        self.response.write(template.render(data))

class SignUp(webapp2.RequestHandler): # sign up for new user
    def get(self):
        user=users.get_current_user()
        instauser_key=ndb.Key('InstaUser',user.user_id())
        instauser=instauser_key.get()
        self.response.headers['Content-Type'] = 'text/html'
        template_values = {
         'users':user
        }
        template = JINJA_ENVIRONMENT.get_template('signUp.html')
        self.response.write(template.render(template_values))
    def post(self):
        user=users.get_current_user()
        Id = self.request.get('userid')
        Name = self.request.get('name')
        abt = self.request.get('about')
        action = self.request.get('button')
        if action=='Sign Up' :
            checkUser = InstaUser.query(InstaUser.userId==Id).fetch()
            if len(checkUser) > 0 :
                self.response.headers['Content-Type'] = 'text/html'
                template_values = {
                 'users':user,
                 'message':'Nickname already exist!',
                 'emailaddress': Name
                }
                template = JINJA_ENVIRONMENT.get_template('signUp.html')
                self.response.write(template.render(template_values))
            else :
                signuser= InstaUser(id=user.user_id(),emailaddress=user.email(),userId=Id,userName=Name,about=abt)
                signuser.put()
                self.redirect('/timeline')
        elif action=='Cancel' :
            url= users.create_login_url('/')
            url_string= 'Login'
            template_values= {
            'url': url,
            'url_string': url_string
            }
            template= JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))

class SearchUser(webapp2.RequestHandler): # render search user profile
    def get(self):
        user = users.get_current_user()
        instaUser = getUserInfo(user) # fetch user data
        username = self.request.get('searchText')
        userinfo = getUserIdfromName(username)  # fetch user data from name
        self.response.headers['Content-Type'] = 'text/html'
        all_post = []
        if userinfo :
            all_post = getAllPostsUser(userinfo.key.id()) # fetch user profile posts
            if userinfo.key.id() !=instaUser['user'].key.id() :
                template_values = {
                  'insta_user':userinfo,
                  'all_posts':all_post,
                  'owner_user':instaUser['user'],
                  'all_user_search':all_users(user.email()),
                }
            else :
                all_post = getAllPostsUser(instaUser['user'].key.id())
                template_values = {
                  'insta_user':instaUser['user'],
                  'all_posts':all_post,
                  'pro_pic_url' : blobstore.create_upload_url('/profilePic'),
                  'all_user_search':all_users(user.email()),
                }
        else :
            all_post = getAllPostsUser(instaUser['user'].key.id())
            template_values = {
              'insta_user':instaUser['user'],
              'all_posts':all_post,
              'pro_pic_url' : blobstore.create_upload_url('/profilePic'),
              'message': 'Searched User Not Found! Loaded your profile!',
              'all_user_search':all_users(user.email()),
            }
        template = JINJA_ENVIRONMENT.get_template('Profile.html')
        self.response.write(template.render(template_values))
class FollowList(webapp2.RequestHandler): # renders follower and following list
    def post(self):
        userId = (self.request.get('id'))
        instaUser = getUserKeyData(userId)
        user=users.get_current_user()
        owner_user = getUserInfo(user)['user']
        action = (self.request.get('mode'))
        listHeader = None
        followingsUsersList = []
        if action=='Following':
            listHeader = 'Following'
            followingsUsersList = getUserFollowingDetails(instaUser) # fetch following user data
        elif action=='Followers' :
            listHeader = 'Followers'
            followingsUsersList = getUserFollowersDetails(instaUser) # fetch followers user data

        self.response.headers['Content-Type'] = 'text/html'

        if userId !=user.user_id() :
            template_values = {
              'insta_user':instaUser,
              'followingsUsersList':followingsUsersList,
              'listHeader':listHeader,
              'owner_user':owner_user,
              'all_user_search':all_users(user.email()),

            }
        else :
            template_values = {
              'insta_user':instaUser,
              'followingsUsersList':followingsUsersList,
              'listHeader':listHeader,
              'all_user_search':all_users(user.email()),
            }

        template = JINJA_ENVIRONMENT.get_template('FollowList.html')
        self.response.write(template.render(template_values))

class FollowUser (webapp2.RequestHandler): # updates user follow and unfollow
    def post(self):
        user=users.get_current_user()
        insta_user = getUserInfo(user)['user']
        follow_user = (self.request.get('id'))
        action = (self.request.get('button'))
        follow_user_data = getUserKeyData((follow_user)) # fetch user data
        if action=='Follow':
            if not insta_user.key.id() in follow_user_data.followers :
                follow_user_data.followers.append(insta_user.key.id())
                follow_user_data.put();
            if not follow_user_data.key.id() in insta_user.following :
                insta_user.following.append(follow_user_data.key.id())
                insta_user.put();
        elif action=='Unfollow':
            if insta_user.key.id() in follow_user_data.followers :
                follow_user_data.followers.remove(insta_user.key.id())
                follow_user_data.put();
            if  follow_user_data.key.id() in insta_user.following :
                insta_user.following.remove(follow_user_data.key.id())
                insta_user.put();

        all_post = getAllPostsUser(follow_user) # fetch user posts
        self.response.headers['Content-Type'] = 'text/html'
        template_values = {
          'insta_user':follow_user_data,
          'all_posts':all_post,
          'owner_user':insta_user,
          'pro_pic_url' : blobstore.create_upload_url('/profilePic'),
          'all_user_search':all_users(user.email()),
        }
        template = JINJA_ENVIRONMENT.get_template('Profile.html')
        self.response.write(template.render(template_values))
class Comment (webapp2.RequestHandler): # makes comments on posts
    def post(self):
        user=users.get_current_user()
        insta_user = getUserInfo(user)['user']
        all_post = []
        page =  (self.request.get('page'))
        if page=='timeline' :
            all_post = getTimeLine(insta_user.key.id()) # fetch timeline posts
        elif page=='profile':
            all_post = getAllPostsUser((self.request.get('profileid'))) # fetch profile posts
        postid = int(self.request.get('postid'))
        commentText = (self.request.get('commentText'))

        stausDt=datetime.datetime.utcnow()+datetime.timedelta(hours=1)
        post_key=ndb.Key('Post',postid)
        post = post_key.get()
        new_comment = Comments(userId=user.user_id(), content=commentText, createdDt=stausDt)
        if all_post :
            for eachpost in all_post :
                if eachpost[0]==postid :
                    comments = eachpost[6]
                    if comments:
                        comments.insert(0, commentToList(new_comment))
                    else:
                        eachpost.append(commentToList(new_comment))

        post.comments.append(new_comment)
        post.put()
        if page=='timeline' :
            template_values = {
             'insta_user': insta_user,
             'all_posts':all_post,
             'comments':eachpost,
             'post_pic_url' : blobstore.create_upload_url('/doPost'),
             'all_user_search':all_users(user.email()),
            }
            template = JINJA_ENVIRONMENT.get_template('Timeline.html')
            self.response.write(template.render(template_values))
            # self.redirect('/timeline')
        elif page=='profile':
            #self.redirect('/profile?id='+profileid)
            user=users.get_current_user()
            instauser_key=ndb.Key('InstaUser',user.user_id())
            instauser=instauser_key.get()
            id =  (self.request.get('profileid'))
            data = getUserKeyData(id)
            self.response.headers['Content-Type'] = 'text/html'
            if id !=user.user_id() :
                template_values = {
                 'insta_user':data,
                 'all_posts':all_post,
                 'owner_user':instauser,
                 'pro_pic_url' : blobstore.create_upload_url('/profilePic'),
                 'all_user_search':all_users(user.email()),
                }
            else:
                template_values = {
                 'insta_user':data,
                 'all_posts':all_post,
                 'pro_pic_url' : blobstore.create_upload_url('/profilePic'),
                 'all_user_search':all_users(user.email()),
                }

            template = JINJA_ENVIRONMENT.get_template('Profile.html')
            self.response.write(template.render(template_values))
def getUserInfo(userid): # Returns user data from userkey
        instauser_key=ndb.Key('InstaUser',userid.user_id())
        instauser=instauser_key.get()
        data = {
            'user' : instauser
        }
        return data

def getUserKeyData (userid): # Returns user data from userkey
        instauser_key=ndb.Key('InstaUser',userid)
        instauser=instauser_key.get()
        return instauser

def getUserKeyFollowingData (userid): # Returns following user data from userkey
        instauser_key=ndb.Key('InstaUser',userid)
        instauser=instauser_key.get()
        return instauser.following


def getUserKey(userid): # Returns user key for user
        instauser_key=ndb.Key('InstaUser',userid)
        instauser=instauser_key.get()
        return instauser.key.id()

def getUserIdfromName(userid): # Returns user data from username
        user = InstaUser.query(InstaUser.userId==userid).fetch()
        if len(user) == 1:
            return user[0]
        else:
            return None

def getAllPostsUser(userid): # Returns all post of users
    finalPostResults = []
    results =  Post.query(Post.userId==userid).order(-Post.createdDt).fetch(50)
    for post in results :
        tempist = []
        finalCommentResults = []
        tempist.append(post.key.id())
        tempist.append(post.content)
        tempist.append(post.createdDt)
        if post.post_pic :
            tempist.append(post.post_pic)
        else :
            tempist.append("")
        post_user = getUserKeyData(post.userId).userName
        if post_user :
            tempist.append(post_user)
        else :
            tempist.append("")
        tempist.append(post.userId)
        if post.comments :
            for com in post.comments :
                com_user = getUserKeyData(com.userId).userName
                commentList = []
                commentList.append(com_user)
                commentList.append(com.content)
                commentList.append(com.createdDt)
                finalCommentResults.append(commentList)
            finalCommentResults.reverse()
            tempist.append(finalCommentResults)
        else :
            tempist.append("")

        finalPostResults.append(tempist)

    return finalPostResults
def getUserFollowingDetails(userData): # Returns user following details
    finalPostResults = []
    if userData.following :
        for user in  userData.following :
            instauser_key=ndb.Key('InstaUser',user)
            instauser=instauser_key.get()
            tempUserList = []
            tempUserList.append(instauser.userId)
            tempUserList.append(instauser.userName)
            tempUserList.append(instauser.key.id())
            finalPostResults.append(tempUserList)
    return finalPostResults

def getUserFollowersDetails(userData): # Returns user followers details
    finalPostResults = []
    if userData.followers :
        for user in  userData.followers :
            instauser_key=ndb.Key('InstaUser',user)
            instauser=instauser_key.get()
            tempUserList = []
            tempUserList.append(instauser.userId)
            tempUserList.append(instauser.userName)
            tempUserList.append(instauser.key.id())
            finalPostResults.append(tempUserList)
    return finalPostResults

def getTimeLine(userid): # Returns user timeline posts
    userFollowings = getUserKeyFollowingData(userid)
    finalFollowList = userFollowings [:]
    finalFollowList.append(userid)
    finalPostResults = []
    if  finalFollowList :
        results = Post.query(Post.userId.IN(finalFollowList)).order(-Post.createdDt).fetch(50)
        for post in results :
            tempist = []
            finalCommentResults = []
            tempist.append(post.key.id())
            tempist.append(post.content)
            tempist.append(post.createdDt)
            if post.post_pic :
                tempist.append(post.post_pic)
            else :
                tempist.append("")
            post_user = getUserKeyData(post.userId).userName
            if post_user :
                tempist.append(post_user)
            else :
                tempist.append("")
            tempist.append(post.userId)
            if post.comments :
                for com in post.comments :
                    com_user = getUserKeyData(com.userId).userName
                    commentList = []
                    commentList.append(com_user)
                    commentList.append(com.content)
                    commentList.append(com.createdDt)
                    finalCommentResults.append(commentList)
                finalCommentResults.reverse()
                tempist.append(finalCommentResults)
            else :
                tempist.append("")

            finalPostResults.append(tempist)


    return finalPostResults

def postToList(new_post) :  # Returns posts as list
    tempist = []
    tempist.append(new_post.key.id())
    tempist.append(new_post.content)
    tempist.append(new_post.createdDt)
    if new_post.post_pic :
        tempist.append(new_post.post_pic)
    else :
        tempist.append("")
    post_user = getUserKeyData(new_post.userId).userName
    if post_user :
        tempist.append(post_user)
    else :
        tempist.append("")
    tempist.append(new_post.userId)

    return tempist

def commentToList(new_comment) : # Returns comments as list
    tempist = []
    com_user = getUserKeyData(new_comment.userId).userName
    tempist.append(com_user)
    tempist.append(new_comment.content)
    tempist.append(new_comment.createdDt)
    return tempist

def all_users(useremail):  # Returns all users details for search
  return InstaUser.query().fetch()
