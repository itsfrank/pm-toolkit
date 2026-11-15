"""Old markdown viewer (renders *.md on localhost:8000)."""
import http.server
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=8000, bind="127.0.0.1")
