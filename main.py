#!/usr/bin/env python

# To commit
# git remote add origin git@github.com:usopyon/macbookconfig.git
# git push origin master

import os
import cgi

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
    user = db.StringProperty()
    name = db.StringProperty()
    url0 = db.StringProperty()
    url1 = db.StringProperty()
    url2 = db.StringProperty()
    type = db.StringProperty()
    TagName = db.StringProperty()
    val1 = db.StringProperty()
    val2 = db.StringProperty()

class NewHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            pass
        template_dict = {
                'user':user.email(),
                'name':'action1',
                'url1':'http://',
                'url2':'',
                'url3':'',
                'all_checked':'checked',
                'tag_checked':'',
                'TagName':'',
                'val1':'1234',
                'val2':'',
                }                
        path = os.path.join(os.path.dirname(__file__),'edit.html')
        self.response.out.write(template.render(path,template_dict))

    def post(self):
        user = users.get_current_user()
        ua = UserAction(
                user = user.email(),
                name = cgi.escape(self.request.get('name')),
                url1 = cgi.escape(self.request.get('url1')),
                url2 = cgi.escape(self.request.get('url2')),
                url3 = cgi.escape(self.request.get('url3')),
                val1 = cgi.escape(self.request.get('val1')),
                val2 = cgi.escape(self.request.get('val2')),
                type = cgi.escape(self.request.get('type')),
                TagName = cgi.escape(self.request.get('TagName')),
                )
        # self.response.out.write(ua.type)
        ua.put()
        self.redirect("/")

class MainHandler(webapp.RequestHandler):
    def get(self):

        link = """
<a href="/new">create action</a><br />
<a href="/isbn/4873113989/dG5pUF9za3NBYWVTblNMc3FxOGxsWHc6MA">
/isbn/formkey</a>
"""
        user = users.get_current_user()
        if user:
            greeting = (u"%s <a href=\"%s\">logout</a>" %\
                    (user.nickname(), users.create_logout_url("/")))
            actions = UserAction.all()
            template_dict = {
                'greeting' : greeting,
                'link' : link,
                'actions':actions
                }
        else:
            greeting = (u"<a href=\"%s\">login</a>" %\
                    users.create_login_url("/"))
            template_dict = {
                'greeting' : greeting,
                'link' : ''
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

        import urllib

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
    ],debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()

