from facebook import get_user_from_cookie, GraphAPI
from threading import Thread

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
        # Get list of all pages managed by the current user
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
        # Get all posts for a page based on their 'is_published' attribute
        args = {'is_published' : published}
        posts = self.api.get_object(page_id+"/promotable_posts",args = args)

        return posts

    def process_posts(self, posts):
        # Given a list of posts, retrieve the number of views for each post and return an array containing 
        # the message and views for each post to be passed on to html.
        # Retrieving views for each post requires a get request, making these requests sequentially
        # creates a large overhead. Therefore, to improve performance each get request is passed to a new
        # thread so that we can make multiple requests simultaneously
        if not posts:
            return None

        threads = []
        processed_posts = []
        index = 0
        view_counts = [0] * len(posts["data"])

        for post in posts["data"]:
            if "message" in post:
                message = post["message"]
            else:
                message = ""

            newthread = Thread(target=self.get_post_viewcount, args=[post['id'], view_counts, index])
            newthread.start()

            threads.append(newthread)

            processed_posts.append({'Message' : message, 'Views' : 0})

        # Wait for all threads to finish before adding results to processed_posts
        for thread in threads:
            thread.join()

        for i in range(len(processed_posts)):
            processed_posts[i]['Views'] = view_counts[i]

        return processed_posts

    def get_post_viewcount(self, post_id, view_counts, index):
        # Given a post id, retrieve the number of views for the post.
        # The results are added to an array at a given index because this function
        # is expected to be called in a separate thread

        views = self.api.get_object(post_id + "/insights/post_impressions_unique")

        if not views["data"]:
            return 

        view_counts[index] = views["data"][0]["values"][0]["value"]