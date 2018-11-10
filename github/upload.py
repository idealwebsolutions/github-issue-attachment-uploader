#!/usr/bin/env python

from lxml.html import fromstring
from asyncio import get_event_loop
from requests import Session
from requests_toolbelt import MultipartEncoder
from mimetypes import guess_type
from fake_useragent import UserAgent
from functools import partial
from os.path import basename
from os import fstat

GITHUB_BASE_URL = 'https://github.com'

GITHUB_LOGIN_ROUTE = 'login'
GITHUB_SESSION_ROUTE = 'session'
GITHUB_NEW_ISSUE_ROUTE = 'issues/new'
GITHUB_ASSETS_ROUTE = 'upload/policies/assets'

async def run_request_flow(loop, fp, config):
    session = Session()
    ua = UserAgent()
    
    # Set user agent for session
    session.headers['user_agent'] = ua.random
        
    # Get auth token for login
    response = await loop.run_in_executor(
        None,
        partial(
            session.get,
            '{}/{}'.format(GITHUB_BASE_URL, GITHUB_LOGIN_ROUTE),
            timeout = 30
        )
    )

    assert response.status_code == 200

    # Parse token and encoding type from form
    tree = fromstring(response.text)

    auth_token = tree.forms[0].fields['authenticity_token']
    utf8 = tree.forms[0].fields['utf8']    

    assert auth_token
    assert utf8
    
    # Sign in
    response = await loop.run_in_executor(
        None,
        partial(
            session.post,
            '{}/{}'.format(GITHUB_BASE_URL, GITHUB_SESSION_ROUTE),
            data = {
                'authenticity_token': auth_token,
                'commit': 'Sign in',
                'login': config['username'],
                'password': config['password'],
                'utf8': utf8
            },
            headers = {
                'content-type': 'application/x-www-form-urlencoded',
                'referer': '{}/{}'.format(GITHUB_BASE_URL, GITHUB_LOGIN_ROUTE)
            },
            timeout = 30
        )
    )

    assert response.status_code == 200

    # Create new "issue"
    response = await loop.run_in_executor(
        None,
        partial(
            session.get,
            '{}/{}/{}/{}'.format(
                GITHUB_BASE_URL,
                config['username'],
                config['repository'],
                GITHUB_NEW_ISSUE_ROUTE
            ),
            timeout = 30
        )
    )

    assert response.status_code == 200
    
    # Parse token and repo id
    tree = fromstring(response.text)

    # TODO: try alt divs in case main element doesnt find attribs
    target = tree.xpath('//file-attachment[contains(@class, "js-upload-markdown-image")]')
    attribs = dict((x, y) for x, y in target[0].items())
    
    img_upload_token = attribs['data-upload-policy-authenticity-token']
    repo_id = attribs['data-upload-repository-id']

    assert img_upload_token
    assert repo_id

    filename = basename(fp.name)
    repository_id = str(repo_id)
    size = str(fstat(fp.fileno()).st_size)
    content_type = guess_type(filename)[0]

    assert filename
    assert size
    assert content_type
    assert repository_id
    
    me = MultipartEncoder(
        fields = {
            'name': filename,
            'size': size,
            'content_type': content_type,
            'authenticity_token': img_upload_token,
            'repository_id': repository_id
        }
    )

    # Issue upload request
    response = await loop.run_in_executor(
        None,
        partial(
            session.post,
            '{}/{}'.format(GITHUB_BASE_URL, GITHUB_ASSETS_ROUTE),
            headers = {
                'referer': '{}/{}/{}/{}'.format(
                    GITHUB_BASE_URL,
                    config['username'],
                    config['repository'],
                    GITHUB_NEW_ISSUE_ROUTE
                ),
                'x-requested-with': 'XMLHttpRequest',
                'content-type': me.content_type,
                'origin': GITHUB_BASE_URL
            },
            data = me,
            timeout = 30
        )
    )

    assert response.status_code == 201

    result = response.json()

    submission_form = result['form']
    asset_url = result['asset']['href']

    file_upload = MultipartEncoder(
        fields = {
            'key': submission_form['key'],
            'AWSAccessKeyId': submission_form['AWSAccessKeyId'],
            'acl': submission_form['acl'],
            'policy': submission_form['policy'],
            'signature': submission_form['signature'],
            'Content-Type': submission_form['Content-Type'],
            'Cache-Control': submission_form['Cache-Control'],
            'x-amz-meta-Surrogate-Control': submission_form['x-amz-meta-Surrogate-Control'],
            'file': (filename, fp, content_type)
        }
    )
    
    # Send upload
    response = await loop.run_in_executor(
        None,
        partial(
            session.post,
            result['upload_url'],
            headers = {
                'content-type': file_upload.content_type,
                'referer': GITHUB_BASE_URL,
                'origin': GITHUB_BASE_URL
            },
            data = file_upload,
            timeout = 60
        )
    )
    
    assert response.status_code == 204
    
    # Print asset link
    print(asset_url)

def start_upload(fp, config):
    loop = get_event_loop()
    loop.run_until_complete(run_request_flow(loop, fp, config))
