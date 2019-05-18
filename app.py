from http.server import HTTPServer, HTTPStatus, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import runpy
import sys
import os
import io
import contextlib
import re
import logging

from datetime import datetime
from time import strftime

logging.basicConfig(format='%(asctime)s %(levelname)7s: %(message)s')
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
  def log_request(self, code='-', size='-'):
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
    
    path = os.path.dirname(os.path.realpath(__file__))

    if parsed_path.endswith('.html'):
      content_type = 'text/html'
      status_code=200
      match = re.findall(r"^(\/.*)?(\/\w+)\.html$", parsed_path)
      (source_path, app) = match[0]
      with open(path + '/template.html', mode='r') as file:
        response = file.read().format(app, source_path).encode('utf-8')
      run_transcrypt('{}/programs{}{}'.format(path, source_path, app))
    elif parsed_path == '/check':
      content_type = 'text/plain'
      status_code=200
      app = parsed_params['app'][0]
      updated_date = os.path.getmtime('{}/programs/{}.py'.format(path, app))
      response = str(datetime.fromtimestamp(updated_date)).encode('utf-8')
    elif parsed_path.endswith('.js'):
      content_type='text/javascript'
      status_code=200
      path_string = '{}{}'
      if '__target__' in parsed_path:
        path_string = '{}/programs{}'
      with open(path_string.format(path, parsed_path), mode='rb') as file:
        response = file.read()

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

