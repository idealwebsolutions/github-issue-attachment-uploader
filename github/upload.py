#!/usr/bin/env python

from requests_toolbelt import MultipartEncoder
from lxml.html import fromstring
from requests import codes, Session

GITHUB_BASE_URL = 'https://github.com'

GITHUB_LOGIN_ROUTE = 'login'
GITHUB_SESSION_ROUTE = 'session'
GITHUB_NEW_ISSUE_ROUTE = 'issues/new'
GITHUB_ASSETS_ROUTE = 'upload/policies/assets'
GITHUB_COMMIT_ACTION = 'Sign in'

FALLBACK_UA = 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'
DEFAULT_TIMEOUT_VALUE = 60

def _finalize_upload(session, upload_url, file_upload_payload):
    """ Finalizes the upload process by uploading file contents """
    response = session.post(
        upload_url,
        headers = {
            'content-type': file_upload_payload.content_type,
            'referer': GITHUB_BASE_URL,
            'origin': GITHUB_BASE_URL
        },
        data = file_upload_payload,
        timeout = DEFAULT_TIMEOUT_VALUE
    )
    if response.status_code != codes.no_content:
        response.raise_for_status()

def _prepare_upload(session, username, repository, request_payload):
    """ Prepares a file upload by creating a new resource """
    response = session.post(
        '{}/{}'.format(GITHUB_BASE_URL, GITHUB_ASSETS_ROUTE),
        headers = {
            'referer': '{}/{}/{}/{}'.format(
                GITHUB_BASE_URL,
                username,
                repository,
                GITHUB_NEW_ISSUE_ROUTE
            ),
            'x-requested-with': 'XMLHttpRequest',
            'content-type': request_payload.content_type,
            'origin': GITHUB_BASE_URL
        },
        data = request_payload,
        timeout = DEFAULT_TIMEOUT_VALUE
    )
    if response.status_code != codes.created:
        response.raise_for_status()
    # Parse JSON response and return form results
    result = response.json()
    # Various fields of this form is necessary to finish the upload properly
    submission_form = result['form']
    # Pick out final upload url
    upload_url = result['upload_url']
    # Save generated asset url
    asset_url = result['asset']['href']
    return (submission_form, upload_url, asset_url)

def _create_new_issue(session, username, repository):
    """ Simulates creating a new issue """
    response = session.get(
        '{}/{}/{}/{}'.format(GITHUB_BASE_URL, username, repository, GITHUB_NEW_ISSUE_ROUTE)
    )
    if response.status_code != codes.ok:
        response.raise_for_status()
    tree = fromstring(response.text)
    # Query for file-attachment element
    root = tree.xpath('//file-attachment[contains(@class, "js-upload-markdown-image")]')
    # Check root contains sub-elements
    if len(root) == 0:
        raise IndexError('Could not find file-attachment element, likely due to invalid login')
    file_attachment = root[0]
    # Find csrf token in subelement (input)
    csrf = file_attachment.find('.//input[@class="js-data-upload-policy-url-csrf"]')
    # Make sure csrf is a valid element
    if csrf is None:
        raise TypeError('CSRF token is missing, unable to continue')
    # Convert attributes to key/value pairs
    attribs = dict((x, y) for x, y in file_attachment.items())
    csrf_attribs = dict((x, y) for x, y in csrf.items())
    # Pick out csrf attribute value
    csrf_token = csrf_attribs['value']
    # Pick out repository id
    repo_id = attribs['data-upload-repository-id']
    return (str(repo_id), csrf_token)

def _basic_login(session, credentials):
    """ Login to Github using basic username/password combo """
    username, password = credentials
    response = session.get('{}/{}'.format(GITHUB_BASE_URL, GITHUB_LOGIN_ROUTE), timeout = 30)
    if response.status_code != codes.ok:
        response.raise_for_status()
    tree = fromstring(response.text)
    # Pick out auth token and utf8 fields for login
    auth_token = tree.forms[0].fields['authenticity_token']
    login_response = session.post(
        '{}/{}'.format(GITHUB_BASE_URL, GITHUB_SESSION_ROUTE), 
        data = {
            'authenticity_token': auth_token,
            'commit': GITHUB_COMMIT_ACTION,
            'login': username,
            'password': password
        }, 
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'referer': '{}/{}'.format(GITHUB_BASE_URL, GITHUB_LOGIN_ROUTE)
        },
        timeout = DEFAULT_TIMEOUT_VALUE
    )
    if login_response.status_code != codes.ok:
        login_response.raise_for_status()

def upload_new_asset(asset, config):
    """ Uploads a new asset to github """
    if type(config) is not dict:
        raise TypeError('config is not a dict')
    filename = config['filename']
    size = config['size']
    content_type = config['content_type']
    # Create new session
    with Session() as session:
        session.headers['user_agent'] = config.get('user-agent') or FALLBACK_UA
        # Login
        _basic_login(session, (config['username'], config['password']))
        # Create new issue and get repo id/csrf token for upload request
        repository_id, csrf_token = _create_new_issue(session, config['username'], config['repository'])
        # Send new asset upload request
        submission_form, upload_url, asset_url = _prepare_upload(
            session, 
            config['username'], 
            config['repository'], 
            MultipartEncoder(
                fields = {
                    'name': filename,
                    'size': size,
                    'content_type': content_type,
                    'authenticity_token': csrf_token,
                    'repository_id': repository_id
                }
            )
        )
        # Finalize asset upload
        _finalize_upload(
            session, 
            upload_url, 
            MultipartEncoder(
                fields = {
                    'key': submission_form['key'],
                    'AWSAccessKeyId': submission_form['AWSAccessKeyId'],
                    'acl': submission_form['acl'],
                    'policy': submission_form['policy'],
                    'signature': submission_form['signature'],
                    'Content-Type': submission_form['Content-Type'],
                    'Cache-Control': submission_form['Cache-Control'],
                    'x-amz-meta-Surrogate-Control': submission_form['x-amz-meta-Surrogate-Control'],
                    'file': (filename, asset, content_type)
                }
            )
        )
        return asset_url
    return None
