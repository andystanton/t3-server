from http.server import HTTPServer, HTTPStatus, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from time import strftime
from pathlib import Path
import runpy
import sys
import os
import io
import contextlib
import re
import logging
import json

logging.basicConfig(format = '%(asctime)s %(levelname)7s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Transcrypt is executed as a module using runpy. It is usually run from 
# the command line so arguments are accepted via sys.argv. The module
# execution also results in a sysexit call which we need to intercept 
# as an error to continue execution of our code. Transcrypt also logs
# directly to stdout, so we need to hijack stdout and log the contents
# of it when Transcrypt is complete.
def run_transcrypt(source):
  f = io.StringIO()
  try:
    if source.endswith('.py'):
      source = source[:-3]
    sys.argv = ['', '-v', '-n', '-b', source]
    with contextlib.redirect_stdout(f):
      runpy.run_module('transcrypt', run_name='__main__')
  except SystemExit as e:
    logger.debug('transcrypt output: {}'.format(f.getvalue()))

class AppRequestHandler(BaseHTTPRequestHandler):
  # Force HTTP/1.1
  protocol_version = 'HTTP/1.1'
  
  # BaseHTTPRequestHandler request logging includes lots of quotes and
  # dashes without context. This function overrides to simplify it.
  def log_request(self, code = '-', size = '-'):
    if isinstance(code, HTTPStatus):
      code = code.value
    self.log_message('%s %s', self.requestline, str(code))
  
  # BaseHTTPRequestHandler writes directly to stderr bypassing the
  # logging configuration. This function overrides to use python logging.
  def log_message(self, format, *args):
    logger.info('{} {}'.format(format%args, self.address_string()))
  
  # BaseHTTPRequestHandler tries to flush the output which we've already 
  # closed resulting in an io error that can be ignored. This function
  # overrides to suppress that error.
  def handle_one_request(self):
    try:
      return BaseHTTPRequestHandler.handle_one_request(self)
    except ValueError as e:
      if str(e) == 'I/O operation on closed file.':
        self.close_connection = True
      else:
        logger.error(e)
        raise e

  def do_GET(self):    
    response = 'not found'.encode('utf-8')
    content_type = 'text/plain'
    status_code = 404
    
    parsed_url = urlparse(self.path)
    parsed_path = parsed_url.path
    parsed_params = parse_qs(parsed_url.query)
    
    t3_path = os.path.dirname(os.path.realpath(__file__))
 
    if parsed_path == '/' or parsed_path == '/index.html':
      with open(t3_path + '/index.html', mode='r') as file:
        response = file.read().encode('utf-8')
      content_type = 'text/html'
      status_code = 200

    elif parsed_path.endswith('.html'):
      (source_path, app) = re.findall(r"^(\/.*)?\/(\w+)\.html$", parsed_path)[0]
      run_transcrypt('{}/programs{}/{}'.format(t3_path, source_path, app))
      with open(t3_path + '/template.html', mode='r') as file:
        response = file.read().format(app, source_path).encode('utf-8')

      content_type = 'text/html'
      status_code = 200

    elif parsed_path.endswith('.js'):
      path_string = '{}/{}'
      if '__target__' in parsed_path:
        path_string = '{}/programs{}'

      with open(path_string.format(t3_path, parsed_path), mode='rb') as file:
        response = file.read()
      content_type = 'text/javascript'
      status_code = 200

    elif parsed_path == '/check':
      app = parsed_params['app'][0]
      updated_date = os.path.getmtime('{}/programs{}.py'.format(t3_path, app))

      response = str(datetime.fromtimestamp(updated_date)).encode('utf-8')
      content_type = 'text/plain'
      status_code = 200

    elif parsed_path == '/programs':
      programs = []
      for filename in Path(t3_path + '/programs').glob('**/*.py'):
        programs.append(str(filename)[len(t3_path + '/programs'):].replace('.py', '.html'))

      response = json.dumps(programs).encode('utf-8')
      content_type = 'text/json'
      status_code = 200

    self.send_response(status_code)
    self.send_header('Content-Type', content_type)
    self.send_header('Content-Length', len(response))
    self.send_header('Cache-Control', 'no-cache')
    self.end_headers()
    self.wfile.write(response)
    self.wfile.close()

def start_server(host = '127.0.0.1', port = 8000):
  server_address = (host, port)
  httpd = HTTPServer(server_address, AppRequestHandler)
  httpd.serve_forever()

def main():
  start_server()

if __name__== "__main__":
  main()

