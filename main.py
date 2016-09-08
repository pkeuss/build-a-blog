#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os
import jinja2
import cgi
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))


class Blogs(db.Model):
    title = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    blogEntry = db.TextProperty(required = True)


class Handler(webapp2.RequestHandler):
    """ A base RequestHandler class for our app.
        The other handlers inherit form this one.
    """

    def renderError(self, error_code):
        """ Sends an HTTP error code and a generic "oops!" message to the client. """

        self.error(error_code)
        self.response.write("Oops! Something went wrong.")


class Index(Handler):
    """ Handles requests coming in to '/' (the root of the site)
    """

    def get(self):
        recent_entries = db.GqlQuery("SELECT * FROM Blogs ORDER BY created desc LIMIT 5")
        t = jinja_env.get_template("blog.html")
        response = t.render(blogs = recent_entries, error = self.request.get("error"))
        self.response.write(response)


class NewEntry(Handler):
    """ Handles requests coming in to '/newpost'
    """
    def write_form(self, title = "", content = "", error = ""):
        t = jinja_env.get_template("newpost.html")
        response = t.render(title = title, content = content, error = self.request.get("error"))
        self.response.write(response)

    def get(self):
        t = jinja_env.get_template("newpost.html")
        response = t.render(error = self.request.get("error"))
        self.response.write(response)

    def post(self):
        new_entry_title = self.request.get("title")
        new_entry_content = self.request.get("content")

        #escape the user's input
        new_entry_title_escaped = cgi.escape(new_entry_title, quote=True)
        new_entry_content_escaped = cgi.escape(new_entry_content, quote=True)

        if(not new_entry_title) or (new_entry_title.strip() == ""):
            error = "please create a title for this post"
            t = jinja_env.get_template("newpost.html")
            response = t.render(content = new_entry_content_escaped, error = cgi.escape(error))
            self.response.write(response)

        # if the user typed nothing at all, redirect and yell at them
        elif (not new_entry_content) or (new_entry_content.strip() == ""):
            error = "Please type the content for this Post."
            t = jinja_env.get_template("newpost.html")
            response = t.render(title = new_entry_title_escaped, error = cgi.escape(error))
            self.response.write(response)


        else:
            # construct a blogs object for the new movie
            blog = Blogs(title = new_entry_title_escaped, blogEntry = new_entry_content_escaped)
            blog.put()
            self.redirect("/blog/" + str(blog.key().id()))

        #self.redirect("/")

class ViewPostHandler(webapp2.RequestHandler):
    def get(self, id):
        entry = Blogs.get_by_id(int(id))
        titleTry = "<h2>" + entry.title + "</h2><br>"
        postTry = "<p>" + entry.blogEntry + "</p><br>"
        linkTry = '<a href="/">MainPage</a>'
        self.response.write(titleTry + postTry + linkTry)

app = webapp2.WSGIApplication([
    ('/', Index),
    ('/newpost', NewEntry),
    webapp2.Route('/blog/<id:\d+>', ViewPostHandler)
], debug=True)
