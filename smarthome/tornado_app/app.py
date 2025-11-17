import os
import tornado.ioloop
import tornado.web
from .config import get_settings
from .handlers.home import HomeHandler
from .handlers.accounts import RegisterHandler, LoginHandler, LogoutHandler
from .handlers.houses import (
    HouseListHandler, AddHouseHandler, AddRoomHandler,
    EditHouseHandler, DeleteHouseHandler,
    EditRoomHandler, DeleteRoomHandler,
    EditHouseInsideHandler, CancelEditHouseInsideHandler
)
from .handlers.profile import (
    ProfileHandler, EditProfileHandler, DeleteProfileHandler
)
from .handlers.error import NotFoundHandler


def make_app():
    settings = get_settings()
    settings["login_url"] = "/login"
    settings["default_handler_class"] = NotFoundHandler
    
    return tornado.web.Application([
        (r"/", HomeHandler),
        (r"/register", RegisterHandler),
        (r"/login", LoginHandler),
        (r"/logout", LogoutHandler),
        (r"/profile", ProfileHandler),
        (r"/profile/edit", EditProfileHandler),
        (r"/profile/delete", DeleteProfileHandler),
        (r"/houses", HouseListHandler),
        (r"/houses/add", AddHouseHandler),
        (r"/houses/add_room", AddRoomHandler),
        (r"/houses/edit_inside/([0-9]+)", EditHouseInsideHandler),
        (r"/houses/edit/([0-9]+)", EditHouseHandler),
        (r"/houses/edit/([0-9]+)/cancel", CancelEditHouseInsideHandler),
        (r"/houses/delete/([0-9]+)", DeleteHouseHandler),
        (r"/rooms/edit/([0-9]+)", EditRoomHandler),
        (r"/rooms/delete/([0-9]+)", DeleteRoomHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler,
         {"path": settings["static_path"]}),
        (r"/media/(.*)", tornado.web.StaticFileHandler,
         {"path": settings["media_path"]}),
    ], **settings)


def main():
    app = make_app()
    port = int(os.getenv("PORT", "8001"))
    app.listen(port)
    print(f"Tornado app running at http://127.0.0.1:{port}")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
