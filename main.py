#!/usr/bin/env python

# To push to github 
# git remote add origin git@github.com:usopyon/macbookconfig.git
# git push origin master

import os
import cgi
import urllib

from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from xml.dom import minidom

import gdata.calendar.service
import gdata.calendar
import gdata.service
import atom.service
import getopt, sys, string, time, atom

import ConfigParser

class UserAction(db.Model):
    user = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    url0 = db.StringProperty(required=True)
    url1 = db.StringProperty()
    type = db.StringProperty(required=True)
    TagName = db.StringProperty()
    val1 = db.StringProperty()

class NewHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect("/") 
            return
        cnt = 0
        while 1:
            name = 'action' + str(cnt)
            uas = UserAction.gql(\
                "WHERE name = :1 AND user = :2 ",\
                name,\
                user.email())
            if uas.count():
                cnt = cnt + 1
            else:
                break

        template_dict = {
                'form_action' : 'new',
                'user':user.email(),
                'name' : name,
                'url0' : 'http://goodsite.cocolog-nifty.com/',
                'val1' : 'uessay/',
                'url1' : 'atom.xml',
                'type':'ByTagName',
                'TagName':'title',
                }                
        path = os.path.join(os.path.dirname(__file__),'edit.html')
        self.response.out.write(template.render(path,template_dict))
        return

    def post(self):
        user = users.get_current_user()
        name = self.request.POST['name']
        uas = UserAction.gql(\
            "WHERE name = :1 AND user = :2 ",\
            name,\
            user.email())
        if uas.count():
            self.response.out.write('Error : <font color="red">')
            self.response.out.write(name)
            self.response.out.write('</font> is used. Please type other name.')
            return
        ua = UserAction(
                user = user.email(),
                name = self.request.POST['name'],
                url0 = self.request.POST['url0'],
                url1 = self.request.POST['url1'],
                type = self.request.POST['type'],
                TagName= self.request.POST['TagName'],
                val1 = self.request.POST['val1'],
                )
        ua.put()
        self.redirect("/")

class EditHandler(webapp.RequestHandler):
    def get(self,user,name):
        current_user = users.get_current_user()
        if not current_user:
            self.redirect("/") 
            return
        query = UserAction.gql(\
                "WHERE name = :1 AND user = :2 ",\
                urllib.unquote_plus(name),\
                urllib.unquote_plus(user))
        ua = query.get()
        template_dict = {
                'ua':ua,
                'form_action':'edit',
                'key':str(ua.key()),
                }
        path = os.path.join(os.path.dirname(__file__),'edit.html')
        self.response.out.write(template.render(path,template_dict))

    def post(self):
        ua = db.get(db.Key(self.request.POST['key']))
        ua.url0 = self.request.POST['url0']
        ua.url1 = self.request.POST['url1']
        ua.type = self.request.POST['type']
        ua.TagName = self.request.POST['TagName']
        ua.val1 = self.request.POST['val1']
        try:
            db.put(ua)
            self.redirect("/")
        except:
            raise

class DeleteHandler(webapp.RequestHandler):
    def get(self,key):
        ua = db.get(db.Key(urllib.unquote_plus(key)))
        ua.delete()
        self.redirect("/")

class UserHandler(webapp.RequestHandler):
    def get(self,user,name):
        query = UserAction.gql(\
            "WHERE name = :1 AND user = :2 ",\
            urllib.unquote_plus(name),\
            urllib.unquote_plus(user))
        ua = query.get()
        url = ua.url0 + ua.val1 + ua.url1
        try:
            xml = urlfetch.fetch(url).content
        except:
            raise
        dom = minidom.parseString(xml)
        if ua.type == 'ByTagName':
            ByTagName = dom.getElementsByTagName(ua.TagName)
            for i in range(100):
                try:
                    self.response.out.write(ByTagName[i].childNodes[0].data)
                    self.response.out.write('\n')
                except:
                    pass
        elif ua.type == 'All':
            self.response.out.write(xml)
        else:
            pass

class MainHandler(webapp.RequestHandler):
    def get(self):

        link = """
<a href="/new">create action</a><br />
"""
        user = users.get_current_user()
        uas = UserAction.all()
        if user:
            greeting = (u"%s <a href=\"%s\">logout</a>" %\
                    (user.nickname(), users.create_logout_url("/")))
            template_dict = {
                'greeting' : greeting,
                'link' : link,
                'uas':uas.filter('user = ',user.email()),
                }
        else:
            greeting = (u"<a href=\"%s\">login</a>" %\
                    users.create_login_url("/"))
            template_dict = {
                'greeting' : greeting,
                'link' : '',
                # 'uas':uas,
                }
        path = os.path.join(os.path.dirname(__file__),'index.html')
        self.response.out.write(template.render(path,template_dict))

class IsbnHandler(webapp.RequestHandler):
    def get(self,isbn,formkey='dG5pUF9za3NBYWVTblNMc3FxOGxsWHc6MA'):

        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        booktitle = self.access_rakuten_api(isbn)
        self.access_google_docs(booktitle,formkey)
        self.access_google_calendar(booktitle)
        self.response.out.write(booktitle)

    def access_rakuten_api(self,isbn):
        config = ConfigParser.ConfigParser()
        config.read('arduinoproxy.config')
        developerId = config.get('rakuten','developerId')
        url = 'http://api.rakuten.co.jp/rws/3.0/rest?'\
            + 'developerId=' + developerId\
            + '&operation=BooksBookSearch'\
            + '&version=2010-03-18'\
            + '&isbn=' + isbn
        try:
            xml = urlfetch.fetch(url).content
            dom = minidom.parseString(xml)
            titles = dom.getElementsByTagName("title")
            subtitles = dom.getElementsByTagName("subTitle")
            rakuten_result = titles[0].childNodes[0].data
            return rakuten_result.encode('utf_8')
        except IndexError:
            return 'Book Not Fount:'+isbn
        except:
            return 'connection failed'

    def access_google_docs(self,booktitle,formkey):

        url = 'http://spreadsheets.google.com/formResponse?'\
                + 'formkey=' + formkey\
                + '&ifq'
        form_fields = {
            "entry.1.single": booktitle,
            "submit": "submit"
        }
        try:
            urlfetch.fetch(url = url,
                payload = urllib.urlencode(form_fields),
                method = urlfetch.POST)
        except:
            self.response.out.write('err:')
            raise

    def access_google_calendar(self,booktitle):

        config = ConfigParser.ConfigParser()
        config.read('arduinoproxy.config')

        calendar_service = gdata.calendar.service.CalendarService()
        calendar_service.email = config.get('google','id')
        calendar_service.password = config.get('google','pw')
        calendar_service.ProgrammaticLogin()
        
        feedURI = 'https://www.google.com/calendar/feeds/'\
                + 't.uehara%40gmail.com'\
                + '/private/full'
        
        event = gdata.calendar.CalendarEventEntry()
        event.title = atom.Title(text = booktitle )
        try:
            new_event = calendar_service.InsertEvent(event, feedURI)
        except:
            self.response.out.write('err:')
            raise

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/isbn/([0-9]{10})/(.*)', IsbnHandler),
        ('/isbn/(.*)', IsbnHandler),
        ('/new', NewHandler),
        ('/edit/(.*)/(.*)', EditHandler),
        ('/edit', EditHandler),
        ('/del/(.*)', DeleteHandler),
        ('/user/(.*)/(.*)', UserHandler),
    ],debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()

