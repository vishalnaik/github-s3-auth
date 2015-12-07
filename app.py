from flask import Flask, redirect, session, request, render_template, url_for, flash, jsonify, send_file, make_response
from helpers.s3 import S3
from helpers.constants import Constants
from helpers.githubuser import GithubUser, PublicGithubUser
from helpers.sources.osenv import OSConstants
import os, time, datetime

app = Flask(__name__)
dev = os.environ.get('dev') == 'true' or not os.environ.get('PORT')
constants = Constants(OSConstants())
app.secret_key = constants.get('SK')

try:
  s3 = S3(constants.get('AWS_ACCESS_KEY'), constants.get('AWS_SECRET_KEY'), constants.get('AWS_BUCKET'))
except:
  s3 = None

def valid_object_key(session):
  if session.get('verified') != True:
    return False
  if session.get('valid_paths') is None:
    return False
  for valid_path in session.get('valid_paths'):
    if is_valid_path(session['object_key'], valid_path):
      return True
  return False

def is_valid_path(user_path, valid_path):
  return user_path.startswith(valid_path) or (user_path + "/").startswith(valid_path)

@app.before_request
def preprocess_request():
  if request.endpoint in {'redirect_view', 'proxy_view', 'pending_view', 'list_view', 'home_view'}:
    if request.view_args.get('object_key'):
      session['object_key'] = request.view_args.get('object_key')
    if session.get('verified') != True:
      session['next'] = request.url
      return redirect(url_for('login_view'))
    if session.get('next'):
      return redirect(session.pop('next'))
    if not s3:
      flash('Your S3 keys are invalid!', 'danger')
      return 'Your S3 keys are invalid!'
    if request.endpoint not in {'home_view'} and valid_object_key(session) != True:
      flash('You do not have access to the requested location!', 'danger')
      return 'You do not have access to the requested location!'

@app.after_request
def postprocess_request(response):
  if not dev:
    response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000')
  return response

def cached(response_data, since, expires=86400):
  response = make_response(response_data)
  response.headers['Last-Modified'] = since
  response.headers['Expires'] = since + datetime.timedelta(seconds=expires)
  if expires > 0:
    response.headers['Cache-Control'] = 'public, max-age={}'.format(expires)
  else:
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
  return response

@app.route('/')
def home_view():
  return render_template('home.html', user_repos = session.get('valid_paths'))

@app.route('/list/<path:object_key>')
def list_view(object_key):
  if session.get('token'):
    response = render_template('list.html', files = s3.get_filelist(object_key), path = object_key)
    return cached(response, datetime.datetime.utcnow(), expires=0)
  else:
    return redirect(url_for('login_view'))

@app.route('/redirect/<path:object_key>')
def redirect_view(object_key):
  url = s3.get_url(object_key, constants.get('EXPIRES'), force_http=constants.get('HTTP') == 'true')
  response = redirect(url if url else url_for('pending_view', object_key=object_key))
  return cached(response, datetime.datetime.utcnow(), expires=0)

@app.route('/proxy/<path:object_key>')
def proxy_view(object_key):
  f, since = s3.get_file(object_key)
  return cached(send_file(f), since) if f else redirect(url_for('pending_view', object_key=object_key))

@app.route('/go/<path:object_key>')
def go_view(object_key):
  url = url_for('{}_view'.format(constants.get('MODE')), object_key=object_key)
  response = redirect('{}?{}'.format(url, request.query_string))
  return cached(response, datetime.datetime.utcnow(), expires=0)

@app.route('/pending/<path:object_key>')
def pending_view(object_key):
  response = render_template('pending.html', object_key=object_key, bucket=constants.get('AWS_BUCKET'), time=time.time())
  return cached(response, datetime.datetime.utcnow(), expires=0)

@app.route('/login')
def login_view():
  session['state'] = str(hash(str(time.time())+constants.get('SK')))
  query = 'client_id={}&scope={}&state={}'.format(
    constants.get('GH_CLIENT_ID'),
    constants.get('GH_SCOPE'),
    session['state'])
  return redirect('https://github.com/login/oauth/authorize?{}'.format(query))

@app.route('/logout')
def logout():
  session.pop('valid_paths', None)
  session.pop('verified', None)
  session.pop('object_key', None)
  return render_template('logged_out.html')

@app.route('/access_denied')
def no_auth_view():
  org_verified = session.get('org_verified', False)
  repo_verified = session.get('repo_verified', False)
  return render_template('no_auth.html', org_verified=org_verified, repo_verified=repo_verified, org=constants.get('GH_ORG_NAME'), repos=[b.repo.name for b in bots.values()])

@app.route('/callback')
def callback_view():
  if request.args.get('state') == session.get('state'):
    code = request.args.get('code')
    user = GithubUser(code=code, client_id=constants.get('GH_CLIENT_ID'), secret=constants.get('GH_SECRET'))
    if user.is_valid():
      session['token'] = user.token
      session['valid_paths'] = list(set(map(lambda x: x + '/', user.get_all_repo_names())).intersection(set(s3.get_all_repo_names())))
      session['verified'] = True
    else:
      flash('Your GitHub credentials are not valid!', 'danger')
      session['verified'] = False
  if session.get('object_key'):
    object_key = session.pop('object_key')
    return redirect(url_for('go_view', object_key=object_key))
  if session.get('next'):
    return redirect(session.pop('next'))
  return redirect(url_for('home_view'))


if __name__ == '__main__':
  if dev:
    app.run(host='0.0.0.0', port=5000, debug=True)
  else:
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT')), debug=False)
