#!/usr/bin/env python

import cgi
import os
import time
import urllib
import logging

from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from xml.dom import minidom

import atom
import atom.service
import gdata.auth
import gdata.alt.appengine
import gdata.calendar
import gdata.calendar.service
import gdata.service
import getopt, sys, string, time, atom

import ConfigParser

HOST_NAME="arduinoproxy.appspot.com"
# HOST_NAME = "localhost:8080"

INTRODUCTION = """
arduino proxy  help Arduino to handle XML and authorization.<br />
<img src="https://cacoo.com/diagrams/n4Mydbj5iWA9M9LR-42D9D.png">
"""

class UserAction(db.Model):
    user = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    url0 = db.StringProperty(required=True)
    url1 = db.StringProperty()
    type = db.StringProperty(required=True)
    TagName = db.StringProperty()
    val1 = db.StringProperty()

class StoredToken(db.Model):
    user_email = db.StringProperty(required=True)
    session_token = db.StringProperty(required=True)

class CalendarHandler(webapp.RequestHandler):
    def __init__(self):
        self.current_user = None
        self.token_scope = None
        self.client = None
        self.token = None

    def post(self):
        event_status = 'not_created'
        event_link = None

        self.current_user = users.GetCurrentUser()

        self.ManageAuth()
        self.LookupToken()

        form = cgi.FieldStorage()

        event = self.InsertEvent(
                form['event_title'].value,)
        if event is not None:
            template_dict = {
                    'debug' : 'Success inserting to calendar',
                    'event_status' : event_status,
                    'event_title' : form['event_title']}
            path = os.path.join(os.path.dirname(__file__),'index.html')
            self.response.out.write(template.render(path,template_dict))

    def get(self):
        self.current_user = users.GetCurrentUser()
        if not self.current_user:
            self.redirect('http://%s/' % (HOST_NAME))
            return

        self.token = self.request.get('token')
        self.ManageAuth()
        self.LookupToken()
        # if self.client.GetAuthSubToken() is not None:
        gast = self.client.GetAuthSubToken()
        logging.info(gast)
        if gast is not None:
            self.feed_url = 'http://www.google.com/calendar/feeds/default/private/full'
            greeting = (u"%s <a href=\"%s\">logout</a>" %(\
                self.current_user.nickname(),
                users.create_logout_url("/cal")))
            template_dict = {
                'authsub':True,
                'user': self.current_user.email(),
                'greeting': greeting,
                'sample_event_title':'sample event',
                }
            path = os.path.join(os.path.dirname(__file__),'index.html')
            self.response.out.write(template.render(path,template_dict))
        else:
            template_dict = {
                'authsub_url': self.client.GenerateAuthSubURL(
                    'http://%s/cal' % (HOST_NAME),
                    'http://www.google.com/calendar/feeds',
                    secure=False, session=True),
                    }
            path = os.path.join(os.path.dirname(__file__),'index.html')
            self.response.out.write(template.render(path,template_dict))

    def ManageAuth(self):
        self.client = gdata.service.GDataService()
        gdata.alt.appengine.run_on_appengine(self.client)
        if self.token:
            self.UpgradeAndStoreToken()

    def LookupToken(self):
        if self.current_user:
            stored_tokens = StoredToken.gql(
                'WHERE user_email = :1',
                self.current_user.email())
            for token in stored_tokens:
                    self.client.SetAuthSubToken(token.session_token)
                    return

    def UpgradeAndStoreToken(self):
        self.client.SetAuthSubToken(self.token)
        self.client.UpgradeToSessionToken()
        if self.current_user:
            new_token = StoredToken(
                    user_email=self.current_user.email(),
                    session_token=self.client.GetAuthSubToken())
            new_token.put()
            self.redirect('http://%s/cal' % (HOST_NAME))

    def InsertEvent(self, title, description=None):
        self.calendar_client = gdata.calendar.service.CalendarService()
        gdata.alt.appengine.run_on_appengine(self.calendar_client)
        self.calendar_client.SetAuthSubToken(self.client.GetAuthSubToken())

        event = gdata.calendar.CalendarEventEntry()
        event.title = atom.Title(text=title)

        try:
            new_event = self.calendar_client.InsertEvent(event,
                    '/calendar/feeds/default/private/full')
            return new_event
        except:
            template_dict = {
                'debug':'You need auth. If continue, click below',
                'authsub_url': self.client.GenerateAuthSubURL(
                    'http://%s/cal' % (HOST_NAME),
                    'http://www.google.com/calendar/feeds',
                    secure=False, session=True),
                        }
            path = os.path.join(os.path.dirname(__file__),'index.html')
            self.response.out.write(template.render(path,template_dict))
            return None

class CalendarInsert(CalendarHandler):
    def get(self, email, title):

        self.current_user = users.GetCurrentUser()
        self.ManageAuth()
        self.LookupToken(email)

        form = cgi.FieldStorage()
        event = self.InsertEvent(title,'')
        logging.info(event)
        if event is not None:
            self.response.out.write('Success to insert event to calendar')

    def LookupToken(self, email):
        stored_tokens = StoredToken.gql(
            'WHERE user_email = :1',email)
        for token in stored_tokens:
            self.client.SetAuthSubToken(token.session_token)
            return

class NewHandler(webapp.RequestHandler):
    def get(self):
        """Set default parameter and display"""
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
                'user': user.email(),
                'name': name,
                'url0': 'http://goodsite.cocolog-nifty.com/',
                'val1': 'uessay/',
                'url1': 'atom.xml',
                'type': 'ByTagName',
                'TagName': 'title',
                }
        path = os.path.join(os.path.dirname(__file__),'edit.html')
        self.response.out.write(template.render(path,template_dict))
        return

    def post(self):
        """db.put() which user input"""
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
    def get(self, user, name):
        """fetch DB and provide editing interface"""
        user = users.get_current_user()
        if not user:
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
        """update UserAction"""
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
    def get(self, key):
        """delete UserAction"""
        ua = db.get(db.Key(urllib.unquote_plus(key)))
        ua.delete()
        self.redirect("/")

class UserHandler(webapp.RequestHandler):
    def get(self, user, name):
        """send get message followed by db"""
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
        if ua.type == 'ByTagName':
            try:
                dom = minidom.parseString(xml)
                ByTagName = dom.getElementsByTagName(ua.TagName)
            except:
                self.response.out.write('Error: check TagName')
                self.response.out.write(sys.exc_info()[0])
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
        """provide main page layout"""
        user = users.get_current_user()
        uas = UserAction.all()
        if user:
            greeting = (u"%s <a href=\"%s\">logout</a>" %\
                    (user.nickname(), users.create_logout_url("/")))
            template_dict = {
                'greeting' : greeting,
                'uas':uas.filter('user = ',user.email()),
                }
        else:
            greeting = (u"<a href=\"%s\">login</a>" %\
                    users.create_login_url("/"))
            template_dict = {
                'greeting' : greeting,
                'link' :INTRODUCTION
                }
        path = os.path.join(os.path.dirname(__file__),'index.html')
        self.response.out.write(template.render(path,template_dict))

class IsbnHandler(webapp.RequestHandler):
    def get(self, isbn, formkey='dG5pUF9za3NBYWVTblNMc3FxOGxsWHc6MA'):
        """get isbn from arduino and send rakuten and google"""
        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        booktitle = self.access_rakuten_api(isbn)
        self.access_google_docs(booktitle,formkey)
        self.access_google_calendar(booktitle)
        self.response.out.write(booktitle)

    def access_rakuten_api(self, isbn):
        """send isbn and get xml and parse"""
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

    def access_google_docs(self, booktitle, formkey):
        """send book title to google spreadsheet"""
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

    def access_google_calendar(self, booktitle):
        """send booktitle to google calendar"""
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
        ('/cal', CalendarHandler),
        ('/cal/(.*)/(.*)', CalendarInsert),
    ],debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()

