import os
import tornado.ioloop
import tornado.web
from .config import get_settings
from .handlers.sensors import (
    SensorsListHandler, SensorDetailHandler, SensorValueHandler
)
from .handlers.equipments import (
    EquipmentsListHandler, EquipmentDetailHandler,
    ShuttersHandler, DoorsHandler, LightsHandler, SoundSystemHandler
)
from .handlers.automation import (
    AutomationRulesHandler, PresenceHandler,
    SensorToEquipmentStatusHandler
)
from .handlers.automation_rules import (
    AutomationRulesListHandler, AutomationRuleDetailHandler
)
from .handlers.users_api import (
    RegisterAPIHandler, LoginAPIHandler, LogoutAPIHandler,
    CurrentUserAPIHandler, UserProfileAPIHandler,
    UploadProfileImageHandler
)
from .handlers.auth_jwt_api import (
    LoginJWTHandler, RegisterJWTHandler
)
from .handlers.houses_api import (
    HousesAPIHandler, HouseDetailAPIHandler,
    RoomsAPIHandler, RoomDetailAPIHandler
)
from .handlers.grid_editor import EditHouseInsideHandler
from .handlers.websocket import RealtimeHandler
from .handlers.house_members import (
    HouseMembersHandler, HouseMemberDetailHandler, MyInvitationsHandler,
    SearchUsersHandler, SearchHousesHandler, RequestHouseAccessHandler
)
from .handlers.event_history import (
    EventHistoryHandler, EventTypesHandler, EventStatsHandler,
    EventCleanupHandler
)
from .handlers.user_positions import UserPositionHandler
from .handlers.weather import WeatherHandler, ValidateAddressHandler


class RedirectHandler(tornado.web.RequestHandler):
    """Redirects old routes to new SPA pages"""
    def initialize(self, url):
        self.redirect_url = url
    
    def get(self):
        self.redirect(self.redirect_url, permanent=False)


class NotFoundHandler(tornado.web.RequestHandler):
    """Handles 404 errors by redirecting to home"""
    def get(self):
        self.redirect("/app/dashboard.html", permanent=False)
    
    def post(self):
        self.redirect("/app/dashboard.html", permanent=False)
    
    def put(self):
        self.redirect("/app/dashboard.html", permanent=False)
    
    def delete(self):
        self.redirect("/app/dashboard.html", permanent=False)


class CustomStaticFileHandler(tornado.web.StaticFileHandler):
    """Custom static file handler that redirects to dashboard on 404"""
    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            self.redirect("/app/dashboard.html", permanent=False)
        else:
            super().write_error(status_code, **kwargs)


def make_app():
    settings = get_settings()
    settings["login_url"] = "/app/login.html"
    settings["default_handler_class"] = NotFoundHandler
    
    return tornado.web.Application([
        # Redirections vers SPA (anciennes routes)
        (r"/", RedirectHandler, {"url": "/app/dashboard.html"}),
        (r"/register", RedirectHandler, {"url": "/app/register.html"}),
        (r"/login", RedirectHandler, {"url": "/app/login.html"}),
        (r"/houses", RedirectHandler, {"url": "/app/dashboard.html"}),
        (r"/profile", RedirectHandler, {"url": "/app/profile.html"}),
        
        # Pages SPA (app statiques)
        (r"/app/(.*)", CustomStaticFileHandler,
         {"path": os.path.join(settings["static_path"], "app")}),
        
        # Éditeur de grille d'intérieur
        (r"/houses/edit_inside/([0-9]+)", EditHouseInsideHandler),
        
        # WebSocket pour les mises à jour en temps réel
        (r"/ws/realtime", RealtimeHandler),
        
        # API REST - Capteurs
        (r"/api/sensors", SensorsListHandler),
        (r"/api/sensors/([0-9]+)", SensorDetailHandler),
        (r"/api/sensors/([0-9]+)/value", SensorValueHandler),
        
        # API REST - Équipements
        (r"/api/equipments", EquipmentsListHandler),
        (r"/api/equipments/([0-9]+)", EquipmentDetailHandler),
        
        # API REST - Contrôle par type d'équipement
        (r"/api/volets", ShuttersHandler),
        (r"/api/portes", DoorsHandler),
        (r"/api/lumieres", LightsHandler),
        (r"/api/sono", SoundSystemHandler),
        
        # API REST - Automatisation B2B
        (r"/api/automation/trigger", AutomationRulesHandler),
        (r"/api/automation/rules", AutomationRulesListHandler),
        (r"/api/automation/rules/([0-9]+)", AutomationRuleDetailHandler),
        (r"/api/presence", PresenceHandler),
        (r"/api/status", SensorToEquipmentStatusHandler),
        
        # API REST - Authentification et utilisateurs
        # Cookie-based auth (legacy)
        (r"/api/auth/register", RegisterAPIHandler),
        (r"/api/auth/login", LoginAPIHandler),
        (r"/api/auth/logout", LogoutAPIHandler),
        (r"/api/auth/me", CurrentUserAPIHandler),
        
        # JWT-based auth (REST API compliant)
        (r"/api/auth/jwt/login", LoginJWTHandler),
        (r"/api/auth/jwt/register", RegisterJWTHandler),
        
        # User profile
        (r"/api/users/([0-9]+)", UserProfileAPIHandler),
        (r"/api/users/([0-9]+)/upload-image", UploadProfileImageHandler),
        
        # API REST - Maisons et pièces
        (r"/api/houses", HousesAPIHandler),
        (r"/api/houses/([0-9]+)", HouseDetailAPIHandler),
        (r"/api/houses/([0-9]+)/rooms", RoomsAPIHandler),
        (r"/api/rooms/([0-9]+)", RoomDetailAPIHandler),
        
        # API REST - Membres de maison
        (r"/api/houses/([0-9]+)/members", HouseMembersHandler),
        (r"/api/houses/([0-9]+)/members/([0-9]+)", HouseMemberDetailHandler),
        (r"/api/houses/([0-9]+)/request-access", RequestHouseAccessHandler),
        (r"/api/invitations", MyInvitationsHandler),
        (r"/api/users/search", SearchUsersHandler),
        (r"/api/houses/search", SearchHousesHandler),
        
        # API REST - Historique des événements
        (r"/api/houses/([0-9]+)/history", EventHistoryHandler),
        (r"/api/houses/([0-9]+)/history/stats", EventStatsHandler),
        (r"/api/houses/([0-9]+)/history/cleanup", EventCleanupHandler),
        (r"/api/event-types", EventTypesHandler),
        
        # API REST - Positions des utilisateurs
        (r"/api/houses/([0-9]+)/positions", UserPositionHandler),
        
        # API REST - Météo
        (r"/api/weather/([0-9]+)", WeatherHandler),
        (r"/api/weather/validate-address", ValidateAddressHandler),
        
        # Fichiers statiques
        (r"/static/(.*)", tornado.web.StaticFileHandler,
         {"path": settings["static_path"]}),
        (r"/media/(.*)", tornado.web.StaticFileHandler,
         {"path": settings["media_path"]}),
    ], **settings)


def main():
    app = make_app()
    port = int(os.getenv("PORT", "8001"))
    app.listen(port, address="0.0.0.0")
    
    print("=" * 60)
    print("🏠 SmartHome Server Started")
    print("=" * 60)
    print(f"📡 Listening on: http://0.0.0.0:{port}")
    print(f"🌐 Local access: http://127.0.0.1:{port}")
    print("=" * 60)
    
    # Afficher l'IP locale pour faciliter l'accès depuis d'autres appareils
    try:
        import socket
        # Créer une socket pour obtenir la vraie IP locale
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"💡 Your local IP: {local_ip}")
        print(f"🔗 Network URL: http://{local_ip}:{port}")
        print("=" * 60)
        print("📱 Access from phone/tablet on same WiFi:")
        print(f"   → http://{local_ip}:{port}")
        print("=" * 60)
    except Exception:
        print("💡 Use 'ifconfig' to find your local IP")
        print("   Your IP is likely: 10.192.138.9")
        print("=" * 60)
    
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
