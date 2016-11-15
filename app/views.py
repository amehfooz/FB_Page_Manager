from facebook import get_user_from_cookie, GraphAPI
from flask import g, render_template, redirect, request, session, url_for
from FbUtils import FbUtils

from app import app, db
from models import User
import requests

# Facebook app details
FB_APP_ID = '1767735720146427'
FB_APP_NAME = 'Mehfooz'
FB_APP_SECRET = '9e1f52e3983ee73d3402ab7e17b392f4'

@app.route('/manage_page',methods=['POST'])
def manage_page():
    # Show options for viewing and submitting posts

    # Take the page id from the form and convert into page using helper class
    # function id_to_page.
    cur_page = request.form['page']
    session['page'] = g.fbutils.id_to_page(cur_page)
    return render_template('manage_page.html')

@app.route('/input_post',methods=['POST'])
def input_post(): 
    # Write a post to the current page on behalf of the page itself.
    # visibility field identifies if this is a published or unpublished post

    message = request.form['message']
    publish = bool(request.form['publish'])
    page_token = session['page']['access_token']
    resp = g.fbutils.post_message(message, page_token, publish)
    return render_template('success.html', post_id = resp['id'])

@app.route('/handle_management_request',methods=['POST'])
def handle_management_request():
    # Redirects to appropriate pages according to the action chosen by user

    # First page of posts are fetched using the FbUtils method get_posts. Views and Message are passed
    # onto html for display.

    # For add, redirected to an html page to input text.

    action = request.form['action']
    
    if 'list' in action:
        if action == 'list-pub':
            published = True
        elif action == 'list-unpub':
            published = False

        page_token = session['page']['access_token']
        page_id = session['page']['id']
        posts = g.fbutils.get_posts(page_id, published)
        processed_posts = g.fbutils.process_posts(posts)

        if 'paging' not in posts:
            posts_next = None
        else:
            posts_next = posts['paging']['next']

        return render_template('display_posts.html', data = processed_posts, next = posts_next, is_published = published)
    elif (action == 'add'): 
        return render_template('input_post.html')

@app.route('/display_next_posts', methods=['POST'])
def display_next_posts():
    # Retrieve next page of posts using requests and pass to FbUtils to get views for each post
    # Views and Message are passed onto html for display.

    next_url = request.form['next']
    posts = requests.get(next_url).json()
    page_token = session['page']['access_token']

    processed_posts = g.fbutils.process_posts(posts)

    if 'paging' not in posts:
        posts_next = None
    else:
        posts_next = posts['paging']['next']
    return render_template('display_posts.html', data = processed_posts, next = posts_next, is_published = published)

@app.route('/pagemanagementredirect')
def pagemanagementredirect():
    # Redirect to page management menu
    return render_template('manage_page.html')

@app.route('/home')
def display_home():
    # Show all the pages a user manages

    pages = g.fbutils.get_pages()
    return render_template('home.html', app_id=FB_APP_ID,app_name=FB_APP_NAME, user=g.user, pages = pages)


#################### BOILER PLATE CODE STARTS HERE ###################

@app.route('/')
def index():
    # If a user was set in the get_current_user function before the request,
    # the user is logged in.

    if g.user:
        return render_template('index.html', app_id=FB_APP_ID,
                               app_name=FB_APP_NAME, user=g.user)
    # Otherwise, a user is not logged in.
    return render_template('login.html', app_id=FB_APP_ID, name=FB_APP_NAME)



@app.route('/logout')
def logout():
    """Log out the user from the application.

    Log out the user from the application by removing them from the
    session.  Note: this does not log the user out of Facebook - this is done
    by the JavaScript SDK.
    """
    session.pop('user', None)
    #g.user = None
    #g.graph = None
    return redirect(url_for('index'))


@app.before_request
def get_current_user():
    """Set g.user to the currently logged in user.

    Called before each request, get_current_user sets the global g.user
    variable to the currently logged in user.  A currently logged in user is
    determined by seeing if it exists in Flask's session dictionary.

    If it is the first time the user is logging into this application it will
    create the user and insert it into the database.  If the user is not logged
    in, None will be set to g.user.
    """

    # Set the user in the session dictionary as a global g.user and bail out
    # of this function early.
    if session.get('user'):
        try:
            g.user = session.get('user')
            g.fbutils = FbUtils(GraphAPI(g.user['access_token']))
        except:
            g.user = None

        return

    # Attempt to get the short term access token for the current user.
    result = get_user_from_cookie(cookies=request.cookies, app_id=FB_APP_ID,
                                  app_secret=FB_APP_SECRET)

    # If there is no result, we assume the user is not logged in.
    if result:
        # Check to see if this user is already in our database.
        user = User.query.filter(User.id == result['uid']).first()

        if not user:
            # Not an existing user so get info
            graph = GraphAPI(result['access_token'])
            g.graph = graph
            profile = graph.get_object('me')
            if 'link' not in profile:
                profile['link'] = ""

            # Create the user and insert it into the database
            user = User(id=str(profile['id']), name=profile['name'],
                        profile_url=profile['link'],
                        access_token=result['access_token'])
            db.session.add(user)
        elif user.access_token != result['access_token']:
            # If an existing user, update the access token
            user.access_token = result['access_token']

        # Add the user to the current session
        session['user'] = dict(name=user.name, profile_url=user.profile_url,
                               id=user.id, access_token=user.access_token)

    # Commit changes to the database and set the user as a global g.user
    db.session.commit()
    g.user = session.get('user', None)
