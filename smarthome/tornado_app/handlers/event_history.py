"""Event History API handlers."""
import tornado.web
from datetime import datetime, timedelta
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from ..models import EventHistory, House, HouseMember, User
from ..database import async_session_maker


class BaseAPIHandler(tornado.web.RequestHandler):
    """Base handler pour les API REST."""

    def check_xsrf_cookie(self):
        """Disable XSRF for REST APIs."""
        pass

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods",
                        "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers",
                        "Content-Type, Authorization")

    def options(self, *args):
        self.set_status(204)
        self.finish()

    def get_current_user(self):
        user_id = self.get_secure_cookie("uid")
        if not user_id:
            return None
        username = self.get_secure_cookie("uname")
        return {
            "id": int(user_id.decode()),
            "username": username.decode() if username else None
        }


class EventHistoryHandler(BaseAPIHandler):
    """Handler pour consulter l'historique des événements."""

    async def get(self, house_id):
        """
        Liste l'historique des événements d'une maison.

        Query parameters:
        - limit: nombre max d'événements (défaut: 50, max: 500)
        - offset: pagination
        - event_type: filtrer par type d'événement
        - days: événements des N derniers jours
        - user_id: filtrer par utilisateur
        """
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Non authentifié"})
            return

        house_id = int(house_id)
        user_id = current_user["id"]

        # Paramètres de requête
        limit = min(int(self.get_argument("limit", "50")), 500)
        offset = int(self.get_argument("offset", "0"))
        event_type = self.get_argument("event_type", None)
        days = self.get_argument("days", None)
        filter_user_id = self.get_argument("user_id", None)

        async with async_session_maker() as session:
            # Vérifier l'accès à la maison
            house = await session.get(House, house_id)
            if not house:
                self.set_status(404)
                self.write({"error": "Maison non trouvée"})
                return

            # Vérifier que l'utilisateur est propriétaire ou membre
            is_owner = house.user_id == user_id
            member_query = select(HouseMember).where(
                and_(
                    HouseMember.house_id == house_id,
                    HouseMember.user_id == user_id,
                    HouseMember.status == 'accepted'
                )
            )
            member_result = await session.execute(member_query)
            is_member = member_result.scalar_one_or_none() is not None

            if not is_owner and not is_member:
                self.set_status(403)
                self.write({"error": "Accès non autorisé"})
                return

            # Construire la requête
            query = select(EventHistory).where(
                EventHistory.house_id == house_id
            )

            # Filtres optionnels
            if event_type:
                query = query.where(EventHistory.event_type == event_type)

            if filter_user_id:
                query = query.where(
                    EventHistory.user_id == int(filter_user_id)
                )

            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=int(days))
                query = query.where(EventHistory.created_at >= cutoff_date)

            # Options de chargement et tri
            query = query.options(
                selectinload(EventHistory.user)
            ).order_by(
                desc(EventHistory.created_at)
            ).limit(limit).offset(offset)

            result = await session.execute(query)
            events = result.scalars().all()

            # Compter le total pour la pagination
            count_query = select(EventHistory).where(
                EventHistory.house_id == house_id
            )
            if event_type:
                count_query = count_query.where(
                    EventHistory.event_type == event_type
                )
            if filter_user_id:
                count_query = count_query.where(
                    EventHistory.user_id == int(filter_user_id)
                )
            if days:
                count_query = count_query.where(
                    EventHistory.created_at >= cutoff_date
                )

            count_result = await session.execute(count_query)
            total = len(count_result.scalars().all())

            events_data = []
            for event in events:
                event_info = {
                    "id": event.id,
                    "event_type": event.event_type,
                    "entity_type": event.entity_type,
                    "entity_id": event.entity_id,
                    "description": event.description,
                    "metadata": event.event_metadata,
                    "created_at": event.created_at.isoformat(),
                    "user_id": event.user_id,
                    "username": event.user.username if event.user else None,
                    "ip_address": event.ip_address
                }
                events_data.append(event_info)

            self.write({
                "events": events_data,
                "total": total,
                "limit": limit,
                "offset": offset
            })


class EventTypesHandler(BaseAPIHandler):
    """Handler pour obtenir la liste des types d'événements."""

    async def get(self):
        """Retourne les types d'événements disponibles."""
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Non authentifié"})
            return
        event_types = {
            "equipment_control": "Contrôle d'équipement",
            "sensor_reading": "Lecture de capteur",
            "member_action": "Action de membre",
            "automation_triggered": "Automatisation déclenchée",
            "house_modified": "Maison modifiée"
        }

        entity_types = {
            "equipment": "Équipement",
            "sensor": "Capteur",
            "member": "Membre",
            "automation_rule": "Règle d'automatisation",
            "house": "Maison",
            "room": "Pièce"
        }

        self.write({
            "event_types": event_types,
            "entity_types": entity_types
        })


class EventStatsHandler(BaseAPIHandler):
    """Handler pour obtenir des statistiques sur l'historique."""

    async def get(self, house_id):
        """
        Retourne des statistiques sur les événements d'une maison.

        Query parameters:
        - days: période en jours (défaut: 7)
        """
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Non authentifié"})
            return

        house_id = int(house_id)
        user_id = current_user["id"]
        days = int(self.get_argument("days", "7"))

        async with async_session_maker() as session:
            # Vérifier l'accès
            house = await session.get(House, house_id)
            if not house:
                self.set_status(404)
                self.write({"error": "Maison non trouvée"})
                return

            is_owner = house.user_id == user_id
            if not is_owner:
                member_query = select(HouseMember).where(
                    and_(
                        HouseMember.house_id == house_id,
                        HouseMember.user_id == user_id,
                        HouseMember.status == 'accepted'
                    )
                )
                member_result = await session.execute(member_query)
                is_member = member_result.scalar_one_or_none() is not None
                if not is_member:
                    self.set_status(403)
                    self.write({"error": "Accès non autorisé"})
                    return

            # Récupérer les événements de la période
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = select(EventHistory).where(
                and_(
                    EventHistory.house_id == house_id,
                    EventHistory.created_at >= cutoff_date
                )
            )
            result = await session.execute(query)
            events = result.scalars().all()

            # Calculer les statistiques
            stats = {
                "total_events": len(events),
                "period_days": days,
                "by_type": {},
                "by_user": {},
                "by_day": {}
            }

            for event in events:
                # Par type
                event_type = event.event_type
                stats["by_type"][event_type] = \
                    stats["by_type"].get(event_type, 0) + 1

                # Par utilisateur
                if event.user_id:
                    stats["by_user"][event.user_id] = \
                        stats["by_user"].get(event.user_id, 0) + 1

                # Par jour
                day_key = event.created_at.strftime("%Y-%m-%d")
                stats["by_day"][day_key] = \
                    stats["by_day"].get(day_key, 0) + 1

            # Ajouter les noms d'utilisateurs
            user_names = {}
            for uid in stats["by_user"].keys():
                user = await session.get(User, uid)
                if user:
                    user_names[uid] = user.username

            stats["user_names"] = user_names

            self.write(stats)


# Fonction helper pour créer des entrées d'historique
async def log_event(session, house_id, user_id, event_type, description,
                    entity_type=None, entity_id=None, metadata=None,
                    ip_address=None):
    """
    Helper pour créer une entrée dans l'historique.

    Args:
        session: SQLAlchemy async session
        house_id: ID de la maison
        user_id: ID de l'utilisateur (peut être None pour actions système)
        event_type: Type d'événement
        description: Description textuelle
        entity_type: Type d'entité concernée (optionnel)
        entity_id: ID de l'entité concernée (optionnel)
        metadata: Données supplémentaires (optionnel)
        ip_address: Adresse IP (optionnel)
    """
    event = EventHistory(
        house_id=house_id,
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        event_metadata=metadata,
        ip_address=ip_address
    )
    session.add(event)
    return event
