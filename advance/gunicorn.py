def app(environ, start_response):
    """
    Simple WSGI application for Gunicorn Hello World example
    """
    data = b"Hello, World!\n"
    status = "200 OK"
    response_headers = [
        ("Content-type", "text/plain"),
        ("Content-Length", str(len(data)))
    ]
    start_response(status, response_headers)
    return [data]

# To run this application with Gunicorn:
# gunicorn -w 4 gunicorn:app
