# github-issues-attachment-uploader
A tool to upload images/files from the command line and generate a direct link without having to create issues on the website. Useful for generating asset links on the go.

# Install
Project uses pipenv to install deps. Tool requires Python 3.6+.

    $ git clone https://github.com/idealwebsolutions/github-issue-attachment-uploader.git
    $ cd github-issue-attachment-uploader
    $ pipenv install

# Usage

    $ pipenv shell
    $ python cli.py <path/to/file> [--repository <name>] [--debug]

First time usage will request user credentials (only username and default repository is stored) to save for future uses (saved in HOME directory as `.gh_upload_attachment`). Passwords will be requested per usage and are not saved/stored ever.

# Gotchas
Supports most common file types with the exception of audio and video

# Support
[Check out the official support article here](https://help.github.com/articles/file-attachments-on-issues-and-pull-requests)

# License
MIT
