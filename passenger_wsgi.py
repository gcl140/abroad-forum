# import os
# import sys


# sys.path.insert(0, os.path.dirname(__file__))


# def application(environ, start_response):
#     start_response('200 OK', [('Content-Type', 'text/plain')])
#     message = 'It works!\n'
#     version = 'Python %s\n' % sys.version.split()[0]
#     response = '\n'.join([message, version])
#     return [response.encode()]


import sys
import os
import imp

# Set path to project root (adjust if needed)
project_home = os.path.dirname(__file__)
sys.path.insert(0, project_home)

# Load the actual WSGI file from your Django project
wsgi = imp.load_source('wsgi', 'forum/wsgi.py')
application = wsgi.application
