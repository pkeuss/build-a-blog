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

# defining this function alows for dynamic limits and offsets in the query statement
def get_posts(limit, offset):
    return db.GqlQuery("SELECT * FROM Blogs ORDER BY created desc LIMIT " + str(limit) + " OFFSET " + str(offset))

# This function takes in the number of posts we want to display per page
# and returns the number of the last page should be based on how many posts
# are in the database
def number_of_pages(post_per_page):
    countBlogs = get_posts(1,0)
    last_page = countBlogs.count() / post_per_page
    needed = countBlogs.count() % post_per_page
    if needed == 0:
        return last_page - 1
    else:
        return last_page

# Declaring the database and its attributes
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
        self.redirect("/blog")


class Blog(Handler):
    """ Handles requests coming in to '/blog' (the unofficial root of the site)
    """

    def get(self):
        page = self.request.get("page")
        perPage = 5

        # if the page number exists in the url, turn it into an int to use
        # later on, otherwise assume you are on the first page
        if page:
            page_num = int(page)
            pageOffset = page_num * perPage
        else:
            page_num = 0
            pageOffset = 0

        # use this function to get the posts that should be displayed on the
        # page we will display for the user
        recent_entries = get_posts(perPage, pageOffset)

        # This function is used to determine the number of the pages we
        # need in order to display all the posts in the database currently
        additional_pages = number_of_pages(perPage)

        # Using the number returned from the previous function call, we determine
        # if the "next" link should be visible and what page number should be
        # associated with the link.  This will be passed to the template to
        # decide what class it should be associated with
        if additional_pages > page_num:
            nextVisible = 'seen'
            next_page = page_num + 1
        else:
            nextVisible = 'unseen'
            next_page = page_num

        # Using the number returned from the previous function call, we determine
        # if the "previous" link should be visible and what page number should be
        # associated with the link
        if page_num == 0:
            previousVisible = 'unseen'
            prev_page = page_num
        else:
            previousVisible = 'seen'
            prev_page = page_num - 1


        # render the template and display in the browser
        t = jinja_env.get_template("blog.html")
        response = t.render(blogs = recent_entries,
                            prev_page = prev_page,
                            next_page = next_page,
                            prev_class = previousVisible,
                            next_class = nextVisible,
                            error = self.request.get("error"))
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
        # render the template and display in the browser
        t = jinja_env.get_template("singleBlog.html")
        response = t.render(entry = entry,
                            error = self.request.get("error"))
        self.response.write(response)

app = webapp2.WSGIApplication([
    ('/', Index),
    ('/blog', Blog),
    ('/newpost', NewEntry),
    webapp2.Route('/blog/<id:\d+>', ViewPostHandler)
], debug=True)
