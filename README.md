# T3 Server

A Python 3 webserver that serves threejs programs written in python and transpiled to javascript by [Transcrypt](http://transcrypt.org). A template html page polls for changes and reloads each program when it detects changes.

It is primarily intended for development of WebGL applications on an iPad without needing an internet connection.

## Quick Start

```
pip install transcrypt
python3 app.py
```

Navigate to http://localhost:8000 to see a list of the available three js programs.

New threejs programs can be added by creating python files in the `/programs` path.

