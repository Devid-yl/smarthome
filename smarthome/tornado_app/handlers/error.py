import tornado.web


class NotFoundHandler(tornado.web.RequestHandler):
    """Handler for 404 errors - redirects to home page."""
    
    def prepare(self):
        """Called before any HTTP method. Redirects to home."""
        self.redirect("/")
