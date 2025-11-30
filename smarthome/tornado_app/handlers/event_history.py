"""Event History API handlers."""

from datetime import datetime, timedelta
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from ..models import EventHistory, House, HouseMember, User
from ..database import async_session_maker
from .base import BaseAPIHandler


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
            self.write({"error": "Not authenticated"})
            return

        house_id = int(house_id)
        user_id = current_user["id"]

        # Query parameters
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
                self.write({"error": "House not found"})
                return

            # Check that the user is owner or member
            is_owner = house.user_id == user_id
            member_query = select(HouseMember).where(
                and_(
                    HouseMember.house_id == house_id,
                    HouseMember.user_id == user_id,
                    HouseMember.status == "accepted",
                )
            )
            member_result = await session.execute(member_query)
            is_member = member_result.scalar_one_or_none() is not None

            if not is_owner and not is_member:
                self.set_status(403)
                self.write({"error": "Access denied"})
                return

            # Build query
            query = select(EventHistory).where(EventHistory.house_id == house_id)

            # Filtres optionnels
            if event_type:
                query = query.where(EventHistory.event_type == event_type)

            if filter_user_id:
                query = query.where(EventHistory.user_id == int(filter_user_id))

            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=int(days))
                query = query.where(EventHistory.created_at >= cutoff_date)

            # Options de chargement et tri
            query = (
                query.options(selectinload(EventHistory.user))
                .order_by(desc(EventHistory.created_at))
                .limit(limit)
                .offset(offset)
            )

            result = await session.execute(query)
            events = result.scalars().all()

            # Compter le total pour la pagination
            count_query = select(EventHistory).where(EventHistory.house_id == house_id)
            if event_type:
                count_query = count_query.where(EventHistory.event_type == event_type)
            if filter_user_id:
                count_query = count_query.where(
                    EventHistory.user_id == int(filter_user_id)
                )
            if days:
                count_query = count_query.where(EventHistory.created_at >= cutoff_date)

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
                    "ip_address": event.ip_address,
                }
                events_data.append(event_info)

            self.write(
                {
                    "events": events_data,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                }
            )


class EventTypesHandler(BaseAPIHandler):
    """Handler pour obtenir la liste des types d'événements."""

    async def get(self):
        """Retourne les types d'événements disponibles."""
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Not authenticated"})
            return
        event_types = {
            "equipment_control": "Contrôle d'équipement",
            "sensor_reading": "Lecture de capteur",
            "member_action": "Action de membre",
            "automation_triggered": "Automatisation déclenchée",
            "house_modified": "Maison modifiée",
        }

        entity_types = {
            "equipment": "Équipement",
            "sensor": "Capteur",
            "member": "Membre",
            "automation_rule": "Règle d'automatisation",
            "house": "Maison",
            "room": "Pièce",
        }

        self.write({"event_types": event_types, "entity_types": entity_types})


class EventCleanupHandler(BaseAPIHandler):
    """Handler pour nettoyer manuellement l'historique."""

    async def post(self, house_id):
        """
        Déclenche un nettoyage manuel de l'historique.
        Réservé au propriétaire de la maison.
        """
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Not authenticated"})
            return

        house_id = int(house_id)
        user_id = current_user["id"]

        async with async_session_maker() as session:
            # Vérifier que l'utilisateur est propriétaire
            house = await session.get(House, house_id)
            if not house:
                self.set_status(404)
                self.write({"error": "House not found"})
                return

            if house.user_id != user_id:
                self.set_status(403)
                self.write({"error": "Only owner can cleanup history"})
                return

            # Effectuer le nettoyage
            result = await cleanup_old_events(session, house_id)

            self.write({"success": True, "cleanup_result": result})


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
            self.write({"error": "Not authenticated"})
            return

        house_id = int(house_id)
        user_id = current_user["id"]
        days = int(self.get_argument("days", "7"))

        async with async_session_maker() as session:
            # Vérifier l'accès
            house = await session.get(House, house_id)
            if not house:
                self.set_status(404)
                self.write({"error": "House not found"})
                return

            is_owner = house.user_id == user_id
            if not is_owner:
                member_query = select(HouseMember).where(
                    and_(
                        HouseMember.house_id == house_id,
                        HouseMember.user_id == user_id,
                        HouseMember.status == "accepted",
                    )
                )
                member_result = await session.execute(member_query)
                is_member = member_result.scalar_one_or_none() is not None
                if not is_member:
                    self.set_status(403)
                    self.write({"error": "Access denied"})
                    return

            # Retrieve les événements de la période
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = select(EventHistory).where(
                and_(
                    EventHistory.house_id == house_id,
                    EventHistory.created_at >= cutoff_date,
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
                "by_day": {},
            }

            for event in events:
                # Par type
                event_type = event.event_type
                stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1

                # Par utilisateur
                if event.user_id:
                    stats["by_user"][event.user_id] = (
                        stats["by_user"].get(event.user_id, 0) + 1
                    )

                # Par jour
                day_key = event.created_at.strftime("%Y-%m-%d")
                stats["by_day"][day_key] = stats["by_day"].get(day_key, 0) + 1

            # Add les noms d'utilisateurs
            user_names = {}
            for uid in stats["by_user"].keys():
                user = await session.get(User, uid)
                if user:
                    user_names[uid] = user.username

            stats["user_names"] = user_names

            self.write(stats)


# Configuration du nettoyage automatique
EVENT_CLEANUP_CONFIG = {
    "max_events_per_house": 1000,  # Nombre max d'événements par maison
    "important_types": [
        "member_action",  # Actions des membres (important)
        "house_modified",  # Modifications maison (important)
        "automation_triggered",  # Automatisations (moyennement important)
    ],
    "low_priority_types": [
        "sensor_reading",  # Lectures de capteurs (moins important)
        "equipment_control",  # Contrôles équipements (moins important)
    ],
    "keep_recent_days": 7,  # Garder tous événements 7 derniers jours
    "keep_important_days": 90,  # Garder événements importants 90 jours
}


async def cleanup_old_events(session, house_id):
    """
    Nettoie les anciens événements d'une maison.

    Stratégie de nettoyage:
    1. Supprime les événements peu importants de plus de 7 jours
    2. Supprime les événements importants de plus de 90 jours
    3. Si total dépasse max après étapes 1-2:
       - Supprime les plus anciens événements peu importants
       - Jusqu'à atteindre 80% du seuil maximum

    Args:
        session: SQLAlchemy async session
        house_id: ID de la maison
    """
    from sqlalchemy import func, delete

    # Compter le nombre total d'événements
    count_query = select(func.count(EventHistory.id)).where(
        EventHistory.house_id == house_id
    )
    count_result = await session.execute(count_query)
    total_events = count_result.scalar()

    # Si on est sous le seuil, pas besoin de nettoyer
    if total_events < EVENT_CLEANUP_CONFIG["max_events_per_house"]:
        return {"deleted": 0, "total": total_events, "reason": "below_threshold"}

    # Dates de coupure
    recent_cutoff = datetime.utcnow() - timedelta(
        days=EVENT_CLEANUP_CONFIG["keep_recent_days"]
    )
    important_cutoff = datetime.utcnow() - timedelta(
        days=EVENT_CLEANUP_CONFIG["keep_important_days"]
    )

    deleted_count = 0

    # ÉTAPE 1: Supprimer événements peu importants de plus de 7 jours
    delete_query = delete(EventHistory).where(
        and_(
            EventHistory.house_id == house_id,
            EventHistory.created_at < recent_cutoff,
            EventHistory.event_type.in_(EVENT_CLEANUP_CONFIG["low_priority_types"]),
        )
    )
    result = await session.execute(delete_query)
    deleted_count += result.rowcount

    # ÉTAPE 2: Supprimer événements importants de plus de 90 jours
    delete_important = delete(EventHistory).where(
        and_(
            EventHistory.house_id == house_id,
            EventHistory.created_at < important_cutoff,
            EventHistory.event_type.in_(EVENT_CLEANUP_CONFIG["important_types"]),
        )
    )
    result_important = await session.execute(delete_important)
    deleted_count += result_important.rowcount

    await session.commit()

    # Recompter après première phase
    count_result = await session.execute(count_query)
    current_total = count_result.scalar()

    # ÉTAPE 3: Si toujours au-dessus du seuil,
    # supprimer les plus anciens événements (peu importants d'abord)
    target_count = int(EVENT_CLEANUP_CONFIG["max_events_per_house"] * 0.8)

    if current_total > EVENT_CLEANUP_CONFIG["max_events_per_house"]:
        to_delete = current_total - target_count

        # D'abord, supprimer les plus anciens événements peu importants
        oldest_low = (
            select(EventHistory.id)
            .where(
                and_(
                    EventHistory.house_id == house_id,
                    EventHistory.event_type.in_(
                        EVENT_CLEANUP_CONFIG["low_priority_types"]
                    ),
                )
            )
            .order_by(EventHistory.created_at)
            .limit(to_delete)
        )

        result = await session.execute(oldest_low)
        ids_to_delete = [row[0] for row in result.all()]

        if ids_to_delete:
            delete_oldest = delete(EventHistory).where(
                EventHistory.id.in_(ids_to_delete)
            )
            result = await session.execute(delete_oldest)
            deleted_count += result.rowcount
            to_delete -= result.rowcount
            await session.commit()

        # Si on doit encore supprimer, prendre les événements importants
        if to_delete > 0:
            oldest_important = (
                select(EventHistory.id)
                .where(
                    and_(
                        EventHistory.house_id == house_id,
                        EventHistory.event_type.in_(
                            EVENT_CLEANUP_CONFIG["important_types"]
                        ),
                    )
                )
                .order_by(EventHistory.created_at)
                .limit(to_delete)
            )

            result = await session.execute(oldest_important)
            ids_to_delete = [row[0] for row in result.all()]

            if ids_to_delete:
                delete_oldest_imp = delete(EventHistory).where(
                    EventHistory.id.in_(ids_to_delete)
                )
                result = await session.execute(delete_oldest_imp)
                deleted_count += result.rowcount
                await session.commit()

    # Recompter final
    count_result = await session.execute(count_query)
    new_total = count_result.scalar()

    return {
        "deleted": deleted_count,
        "total_before": total_events,
        "total_after": new_total,
        "target": target_count,
        "reason": "automatic_cleanup",
    }


# Fonction helper pour créer des entrées d'historique
async def log_event(
    session,
    house_id,
    user_id,
    event_type,
    description,
    entity_type=None,
    entity_id=None,
    metadata=None,
    ip_address=None,
):
    """
    Helper pour créer une entrée dans l'historique.
    Effectue un nettoyage automatique si nécessaire.

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
        ip_address=ip_address,
    )
    session.add(event)

    # Déclencher nettoyage automatique toutes les 100 insertions
    import random

    if random.randint(1, 100) == 1:
        await cleanup_old_events(session, house_id)

    return event
