from facebook import get_user_from_cookie, GraphAPI
from threading import Thread
import time

class FbUtils:
    def __init__(self, api):
        self.api = api

        # Get all the pages using Facebook SDK function call
        self.page_list = self.api.get_object('me/accounts')['data']

        # Set up page lookup table for optimized lookup from page id
        self.page_lookup = {}

        for page in self.page_list:
            self.page_lookup[page['id']] = page

    def get_pages(self):
        return self.page_list

    def id_to_page(self, page_id):
        # Return page from lookup table using page id

        return self.page_lookup[page_id]


    def post_message(self, msg, page_token, published):
        # Post to page on behalf of the page
        # The boolean 'published' specifies if the post is
        # published or unpublished

        page_api = GraphAPI(page_token)
        attributes = {'published' : published}
        return page_api.put_wall_post(msg,attachment=attributes);
        
    def get_posts(self, page_id, published):
        args = {'is_published' : published}
        posts = self.api.request(page_id+"/promotable_posts",args = args)

        return posts

    def process_posts(self, posts):
        if not posts:
            return None

        processed_posts = []

        for post in posts["data"]:
            if "message" in post:
                message = post["message"]
            else:
                message = ""

            view_count = self.get_post_viewcount(post["id"])
            processed_posts.append({'Message' : message, 'Views' : view_count})

        return processed_posts

    def get_post_viewcount(self, post_id):
        views = self.api.get_object(post_id + "/insights/post_impressions_unique")

        if not views["data"]:
            return 0

        return views["data"][0]["values"][0]["value"]