#!/usr/bin/env python

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch
from xml.dom import minidom

# for gdata

import gdata.calendar.service
import gdata.calendar
import gdata.service
import atom.service
import getopt, sys, string, time, atom

import ConfigParser

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        self.response.out.write('<a href="/isbn/4873113989">isbn</a><br/ >')
        self.response.out.write('<a href="/isbn/4873113989/dG5pUF9za3NBYWVTblNMc3FxOGxsWHc6MA">isbn/formkey</a>')

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
        url = 'http://api.rakuten.co.jp/rws/3.0/rest?developerId='+developerId+'&operation=BooksBookSearch&version=2010-03-18&isbn=' + isbn
        try:
            xml = urlfetch.fetch(url).content
        except:
            return 'connection failed'
        dom = minidom.parseString(xml)
        titles = dom.getElementsByTagName("title")
        subtitles = dom.getElementsByTagName("subTitle")
        try:
            rakuten_result = titles[0].childNodes[0].data
            return rakuten_result.encode('utf_8')
        except IndexError:
            return 'Book Not Fount:'+isbn

    def access_google_docs(self,booktitle,formkey):

        # via http://code.google.com/intl/ja/appengine/docs/python/urlfetch/overview.html
        import urllib

        # self.response.out.write(formkey)

        url = 'http://spreadsheets.google.com/formResponse?formkey='+formkey+'&ifq'
        form_fields = {
            "entry.1.single": booktitle,
            "submit": "submit"
        }
        try:
            urlfetch.fetch(url = url,
                payload = urllib.urlencode(form_fields),
                method = urlfetch.POST)
        except:
            raise

    def access_google_calendar(self,booktitle):

        config = ConfigParser.ConfigParser()
        config.read('arduinoproxy.config')

        calendar_service = gdata.calendar.service.CalendarService()
        calendar_service.email = config.get('google','id')
        calendar_service.password = config.get('google','pw')
        calendar_service.source = 'Example-Example-1'
        calendar_service.ProgrammaticLogin()
        
        feedURI = 'https://www.google.com/calendar/feeds/t.uehara%40gmail.com/private/full'
        start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z',time.gmtime())
        end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z',time.gmtime(time.time() + 3600))
        
        event = gdata.calendar.CalendarEventEntry()
        event.title = atom.Title(text = booktitle )
        event.content = atom.Content(text = 'TestContent')
        event.when.append(gdata.calendar.When(start_time = start_time, end_time = end_time ))
        new_event = calendar_service.InsertEvent(event, feedURI)

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/isbn/([0-9]{10})/(.*)', IsbnHandler),
        ('/isbn/(.*)', IsbnHandler),
    ],debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
