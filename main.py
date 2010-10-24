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

class IsbnHandler(webapp.RequestHandler):
    def get(self,isbn):
        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        booktitle = self.access_rakuten_api(isbn)
        self.access_google_docs(booktitle)
        # self.access_google_calendar(booktitle)
        self.response.out.write(booktitle)

    def access_rakuten_api(self,isbn):
        config = ConfigParser.ConfigParser()
        config.read('arduinoproxy.config')
        developerId = config.get('rakuten','developerId')
        url = 'http://api.rakuten.co.jp/rws/3.0/rest?developerId='+developerId+'&operation=BooksBookSearch&version=2010-03-18&isbn=' + isbn
        xml = urlfetch.fetch(url).content
        dom = minidom.parseString(xml)
        titles = dom.getElementsByTagName("title")
        subtitles = dom.getElementsByTagName("subTitle")
        rakuten_result = titles[0].childNodes[0].data
        return rakuten_result.encode('utf_8')

    def access_google_docs(self,booktitle,formkey='dG5pUF9za3NBYWVTblNMc3FxOGxsWHc6MA'):

        # via http://code.google.com/intl/ja/appengine/docs/python/urlfetch/overview.html
        import urllib
        
        form_fields = {
            "entry.1.single": booktitle,
            "submit": "submit"
        }
        urlfetch.fetch(url = 'http://spreadsheets.google.com/formResponse?formkey='+formkey+'&ifq',
            payload = urllib.urlencode(form_fields),
            method = urlfetch.POST)
        
    def access_google_calendar(self,booktitle):

        config = ConfigParser.ConfigParser()
        config.read('arduinoproxy.config')

        calendar_service = gdata.calendar.service.CalendarService()
        calendar_service.email = 't.uehara@gmail.com'
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
        ('/isbn/(.*)', IsbnHandler),
        ('/isbn/(.*)/(.*)', IsbnHandler),
    ],debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
