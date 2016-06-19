import time

from flask import Flask, flash, redirect,render_template, request, session
from flask_oauth import OAuth
from wtforms import Form, StringField

from analyze import analyze_followers
from analyze import analyze_friends

app = Flask('twitter-gender-ratio')
oauth = OAuth()
twitter = oauth.remote_app(
    'twitter',
    base_url='https://api.twitter.com/1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key="XpukwJDDIXoF1iBcTAJMXYthg",
    consumer_secret="wVuS3bj6hHCuoTkMEqAHjl0l2bODcLRIXkvs2JzOYxfGERYskq")


@twitter.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')


@app.route('/login')
def login():
    callback = '/authorized'
    next_url = request.args.get('next') or request.referrer
    if next_url:
        callback += '?next=' + next_url

    return twitter.authorize(callback=callback)


@app.route('/logout')
def logout():
    session.pop('twitter_token')
    session.pop('twitter_user')
    return redirect('/')


@app.route('/authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
    next_url = request.args.get('next') or '/'
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    session['twitter_token'] = (resp['oauth_token'], resp['oauth_token_secret'])
    session['twitter_user'] = resp['screen_name']
    flash('You were signed in as %s' % resp['screen_name'])
    return redirect(next_url)


class AnalyzeForm(Form):
    user_id = StringField('Twitter User Name')


@app.route('/', methods=['GET', 'POST'])
def index():
    oauth_token, oauth_token_secret = session.get('twitter_token', (None, None))
    form = AnalyzeForm(request.form)
    results = {}
    error = None
    if request.method == 'POST' and form.validate() and form.user_id.data:
        if app.config['DRY_RUN']:
            time.sleep(2)
            results = {'friends': (150, 25, 200),
                       'followers': (200, 20, 250)}
        else:
            try:
                results = {'friends': analyze_friends(form.user_id.data,
                                                      oauth_token,
                                                      oauth_token_secret),
                           'followers': analyze_followers(form.user_id.data,
                                                          oauth_token,
                                                          oauth_token_secret)}
            except Exception as exc:
                error = exc

    return render_template('index.html',
                           form=form, results=results, error=error)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('port', nargs=1, type=int)
    args = parser.parse_args()
    [port] = args.port

    app.config['DRY_RUN'] = args.dry_run
    app.config['SECRET_KEY'] = 'f1e8922a-ea9a-4f6a-aad1-08071e10e0da'
    app.run(port=port, debug=args.debug)