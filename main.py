#!/usr/bin/env python
# -*- coding: utf-8 -*-

HOST_NAME="arduinoproxy.appspot.com"
HOST_NAME = "localhost:8080"

INTRODUCTION = """
arduino proxy  help Arduino to handle XML and authorization.<br />
If you login this site, you can create UserAction which is<br />
invisible from others and insert Google Calendar.
"""
import atom,atom.service
import cgi,cgitb
import logging
import urllib

import ConfigParser

import gdata.auth
import gdata.alt.appengine
import gdata.calendar
import gdata.calendar.service
import gdata.service

from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from xml.dom import minidom

class UserAction(db.Model):
    user = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    desc = db.TextProperty()
    fetch = db.BooleanProperty()
    url0 = db.StringProperty()
    url1 = db.StringProperty()
    val1 = db.StringProperty()
    type = db.StringProperty(required=True)
    TagName = db.StringProperty()
    NodeNum = db.IntegerProperty()
    editable = db.BooleanProperty()
    gcal = db.BooleanProperty()
    gdoc = db.BooleanProperty()
    formkey = db.StringProperty()

    def set_optional_value(self, form):

        self.fetch = False
        if form.getfirst('fetch'):
            self.fetch = True

        self.desc = ''
        if form.has_key('desc'):
            self.desc = unicode(form['desc'].value,'utf_8')

        self.url0 = ''
        if form.has_key('url0'):
            self.url0 = form['url0'].value

        self.url1 = ''
        if form.has_key('url1'):
            self.url1 = form['url1'].value

        self.TagName = ''
        if form.has_key('TagName'):
            self.TagName = form['TagName'].value

        self.NodeNum = 0
        if form.has_key('NodeNum'):
            self.NodeNum = int(form['NodeNum'].value)

        self.val1 = ''
        if form.has_key('val1'):
            self.val1 = form['val1'].value

        self.gcal = False
        if form.getfirst('gcal'):
            self.gcal= True

        self.gdoc = False
        if form.getfirst('gdoc'):
            self.gdoc = True

        self.formkey=''
        if form.getfirst('formkey'):
            self.formkey = form['formkey'].value
        self.put()

    def testurl(self):
        return 'http://' + HOST_NAME + '/user/'\
                + str(self.key()) + '/' + self.val1

class StoredToken(db.Model):
    user_email = db.StringProperty(required=True)
    session_token = db.StringProperty(required=True)

class UaCommon():
    def __init__(self):
        self.user = users.get_current_user()
        if not self.user:
            self.user = users.User('anonymous')

    def show_message(self, str):
        template_dict = { 'message' : str }
        self.response.out.write(template.render('blank.html',template_dict))

    def is_name_unique(self, name):
        uas = UserAction.gql(
                "WHERE name = :1 AND user = :2 ", name, self.user.email())
        if uas.count() > 0:
            self.show_message(name + ' is used. Please type other name.')
            return 0
        else:
            return 1

    def google_docs(self, str, formkey='dG5pUF9za3NBYWVTblNMc3FxOGxsWHc6MA'):
        """send book title to google spreadsheet"""
        url = 'http://spreadsheets.google.com/formResponse?'\
                + 'formkey=' + formkey.rstrip() + '&ifq'
        form_fields = {
            "entry.1.single": str.rstrip(),
            "submit": "submit"
        }
        try:
            urlfetch.fetch(url = url,
                payload = urllib.urlencode(form_fields),
                method = urlfetch.POST)
        except:
            raise

class NewHandler(UaCommon,webapp.RequestHandler):
    def __init__(self):
        UaCommon.__init__(self)

    def get(self):
        """Set default parameter and display"""
        cnt = 0
        while 1:
            name = 'action' + str(cnt)
            uas = UserAction.gql(\
                "WHERE name = :1 AND user = :2 ",\
                name,self.user.email())
            if uas.count():
                cnt = cnt + 1
            else:
                break
        template_dict = {
                'hostname' : HOST_NAME,
                'action' : 'new',
                'user': self.user.email(),
                'name': name,
                'desc': 'Write here description',
                'fetch': True,
                'url0': 'http://arduino.cc/',
                'val1': 'blog',
                'url1': '/feed/',
                'type': 'ByTagName',
                'TagName': 'title',
                'NodeNum': 0,
                }
        self.response.out.write(template.render('edit.html',template_dict))
        return

    def post(self):
        """db.put() which user input"""
        form = cgi.FieldStorage()
        name = unicode(form['name'].value,'utf_8')
        if self.is_name_unique(name) == 0 :
            return
        try:
            ua = UserAction(
                user = self.user.email(),
                name = name,
                url0 = form['url0'].value,
                type = form['type'].value,
                editable = True
            )
            ua.set_optional_value(form)
            ua.put()
        except:
            self.response.out.write(cgitb.handler())
            raise
        self.show_message('Success! Use this URL to paste Arduino code<br />\
                    <input type="text" size = "70" value="' + ua.testurl() + '">')
        return

class EditHandler(UaCommon,webapp.RequestHandler):
    def get(self, key ):
        """fetch DB and provide editing interface"""
        ua = db.get(db.Key(urllib.unquote_plus(key)))
        template_dict = {
                'hostname' : HOST_NAME,
                'ua': ua,
                'action': 'edit',
                'key': str(ua.key()),
                }
        self.response.out.write(template.render('edit.html',template_dict))

    def post(self):
        """update UserAction"""
        form = cgi.FieldStorage()
        for p in ['key','name','url0','type']:
            if form.has_key(p) is False:
                self.show_message('You must input marked inputbox')
                return
        try:
            ua = db.get(db.Key(form['key'].value))
            ua.name = unicode(form['name'].value,'utf_8')
            ua.url0 = form['url0'].value
            ua.type = form['type'].value
            ua.set_optional_value(form)
            db.put(ua)
            self.show_message('Updated! Use this URL to paste Arduino code<br />\
                    <input type="text" size = "70" value="' + ua.testurl() + '">')
        except:
            self.response.out.write(cgitb.handler())
            raise

class DeleteHandler(webapp.RequestHandler):
    def get(self, key):
        """delete UserAction"""
        ua = db.get(db.Key(urllib.unquote_plus(key)))
        ua.delete()
        self.redirect("/")

class UserHandler(UaCommon,webapp.RequestHandler):
    def get(self, key, val1=''):
        """send get message followed by db"""
        ua = db.get(db.Key(urllib.unquote_plus(key)))
        url = ua.url0.rstrip() + urllib.unquote(val1.rstrip())\
                + ua.url1.rstrip()
        str = ''
        try:
            xml = urlfetch.fetch(url).content
        except:
            self.response.out.write(cgitb.handler())
            raise
        if ua.type == 'ByTagName':
            try:
                dom = minidom.parseString(xml)
                ByTagName = dom.getElementsByTagName(ua.TagName)
                #str = ByTagName[0].childNodes[0].data
                str = ByTagName[ua.NodeNum].childNodes[0].data
            except:
                self.response.out.write(cgitb.handler())
        elif ua.type == 'All':
            str = xml
        else:
            pass
        self.response.out.write(str)
        if ua.gdoc:
            self.google_docs(str, ua.formkey)

class MainHandler(webapp.RequestHandler):

    def get(self):
        """provide main page layout"""
        user = users.get_current_user()
        uas =  UserAction.all()
        if user:
            greeting = (u"%s <a href=\"%s\">logout</a>" %\
                    (user.nickname(), users.create_logout_url("/")))
            template_dict = {
                'greeting' : greeting,
                'uas':uas.filter('user = ',user.email()),
                }
        else:
            user = users.User('anonymous')
            greeting = (u"<a href=\"%s\">login</a>" %\
                    users.create_login_url("/"))
            template_dict = {
                'greeting' : greeting,
                'anonymous' : 'anonymous',
                'uas':uas.filter('user = ',user.email()),
                'link' :INTRODUCTION
                }
        self.response.out.write(template.render('index.html',template_dict))

class IsbnHandler(UaCommon,webapp.RequestHandler):
    def get(self, isbn, formkey='dG5pUF9za3NBYWVTblNMc3FxOGxsWHc6MA'):
        """get isbn from arduino and send rakuten and google"""
        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        booktitle = self.access_rakuten_api(isbn)
        self.google_docs(booktitle,formkey)
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

    def access_google_calendar(self, booktitle):
        """send booktitle to google calendar"""
        config = ConfigParser.ConfigParser()
        config.read('arduinoproxy.config')

        calendar_service = gdata.calendar.service.CalendarService()
        calendar_service.email = config.get('google','id')
        calendar_service.password = config.get('google','pw')
        calendar_service.ProgrammaticLogin()
        feedURI = 'https://www.google.com/calendar/feeds/'\
                + urllib.quote(config.get('google','id'))\
                + '/private/full'
        event = gdata.calendar.CalendarEventEntry()
        event.title = atom.Title(text = booktitle )
        try:
            new_event = calendar_service.InsertEvent(event, feedURI)
        except:
            self.response.out.write('err:')
            raise

class CalendarSetting(webapp.RequestHandler):
    def __init__(self):
        self.current_user = None
        self.token_scope = None
        self.client = None
        self.token = None

    def post(self):
        """post method is to check from setting page"""
        self.ManageAuth()
        self.LookupToken()
        form = cgi.FieldStorage()
        event = self.InsertEvent(form['event_title'].value)
        if event is not None:
            template_dict = {
                    'debug' : 'Success inserting to calendar',
                    'event_title' : form['event_title']}
            self.response.out.write(template.render('index.html',template_dict))

    def get(self):
        """provide calendar setting page via login status"""
        self.current_user = users.get_current_user()
        if not self.current_user:
            self.redirect('http://%s/' % (HOST_NAME))
            return

        self.token = self.request.get('token')
        self.ManageAuth()
        self.LookupToken()
        if self.client.GetAuthSubToken() is not None:
            self.feed_url = 'http://www.google.com/calendar/feeds/default/private/full'
            greeting = (u"%s <a href=\"%s\">logout</a>" %(\
                self.current_user.nickname(),
                users.create_logout_url("/cal")))
            template_dict = {
                'authsub':True,
                'user': self.current_user.email(),
                'host_name': HOST_NAME,
                'greeting': greeting,
                }
            self.response.out.write(template.render('index.html',template_dict))
        else:
            template_dict = {
                'authsub_url': self.client.GenerateAuthSubURL(
                    'http://%s/cal' % (HOST_NAME),
                    'http://www.google.com/calendar/feeds',
                    secure=False, session=True),
                    }
            self.response.out.write(template.render('index.html',template_dict))

    def ManageAuth(self):
        self.client = gdata.service.GDataService()
        gdata.alt.appengine.run_on_appengine(self.client)
        if self.token:
            self.client.SetAuthSubToken(self.token)
            self.client.UpgradeToSessionToken()
            if self.current_user:
                new_token = StoredToken(
                        user_email=self.current_user.email(),
                        session_token=self.client.GetAuthSubToken())
                new_token.put()
                self.redirect('http://%s/cal' % (HOST_NAME))

    def LookupToken(self):
        if self.current_user:
            stored_tokens = StoredToken.gql(
                'WHERE user_email = :1',
                self.current_user.email())
            for token in stored_tokens:
                    self.client.SetAuthSubToken(token.session_token)
                    return

    def InsertEvent(self, title, description=None):
        """This func is called on calendar setting page"""
        self.calendar_client = gdata.calendar.service.CalendarService()
        gdata.alt.appengine.run_on_appengine(self.calendar_client)
        self.calendar_client.SetAuthSubToken(self.client.GetAuthSubToken())
        event = gdata.calendar.CalendarEventEntry()
        event.title = atom.Title(text=title)

        try:
            new_event = self.calendar_client.InsertEvent(
                event,'/calendar/feeds/default/private/full')
            return new_event
        except:
            template_dict = {
                'debug': 'You need auth. If continue, click below',
                'authsub_url': self.client.GenerateAuthSubURL(
                    'http://%s/cal' % (HOST_NAME),
                    'http://www.google.com/calendar/feeds',
                    secure=False, session=True),
                        }
            self.response.out.write(template.render('index.html',template_dict))
            return None

class CalendarInsert(CalendarSetting):
    def get(self, email, title):
        """direct insert title to calender"""
        self.current_user = users.get_current_user()
        self.ManageAuth()
        self.LookupToken(email)
        form = cgi.FieldStorage()
        event = self.InsertEvent(title,'')
        if event is not None:
            self.response.out.write('Success to insert event to calendar')

    def LookupToken(self, email):
        """override for direct. Because direct usage have current_user"""
        stored_tokens = StoredToken.gql(
            'WHERE user_email = :1',email)
        for token in stored_tokens:
            self.client.SetAuthSubToken(token.session_token)
            return

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/isbn/([0-9]{10})/(.*)', IsbnHandler),
        ('/isbn/(.*)', IsbnHandler),
        ('/new', NewHandler),
        ('/edit/(.*)', EditHandler),
        ('/edit', EditHandler),
        ('/del/(.*)', DeleteHandler),
        ('/user/([0-9a-zA-Z]{1,99})/(.*)', UserHandler),
        ('/user/(.*)', UserHandler),
        ('/cal', CalendarSetting),
        ('/cal/(.*)/(.*)', CalendarInsert),
    ],debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()

