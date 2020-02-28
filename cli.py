#!/usr/bin/env python

from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from os.path import expanduser, join, exists
from os import environ
from getpass import getpass
from logging import basicConfig, getLogger, disable, DEBUG
from github.upload import upload_new_asset

basicConfig(level=DEBUG)
logger = getLogger(__name__)
configfile = join(expanduser('~'), '.gh_upload_attachment')

def load_config(path):
    config = ConfigParser()

    if not exists(path):
        logger.debug('Config does not exist. Creating new config file...')
        # Ask for inputs
        username = input('Github username: ')
        password = getpass('Github password: ')
        repository = input('Default repository: ')

        config['credentials'] = { 'username': username }
        config['repository'] = { 'name': repository }
        
        try:
            with open(path, 'w') as f:
                config.write(f)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception:
            logger.error('Unable to open/write file', exc_info=True)

        return {
            'username': username, 
            'password': password, 
            'repository': repository
        }
    
    logger.debug('Config file found...')
    
    try:
        with open(path) as f:
            config.read_file(f)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception:
        logger.error('Unable to open/read file', exc_info=True)

    password = getpass('Github password: ')

    return {
        'username': config.get('credentials', 'username'),
        'password': password,
        'repository': config.get('repository', 'name')
    }

def main():
    parser = ArgumentParser(
        description='A tool to upload files/images to github via issues'
    )
    parser.add_argument(
        '--repository', 
        nargs=1,
        type=str, 
        help='repository to use (name of repo)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='debug process'
    )
    parser.add_argument(
        'file',
        nargs=1,
        type=FileType('rb'),
        help='file to be uploaded'
    )

    args = parser.parse_args()
    
    # Disable logging if not in debug mode
    if not args.debug:
        disable(DEBUG)

    # Parse config
    config = load_config(configfile)
    
    # Use selected repository instead of default
    if args.repository:
        config['repository'] = args.repository[0]

    # Begin uploading
    print(upload_new_asset(args.file[0], config))

if __name__ == '__main__':
    main()
