"""House Members API handlers."""
import tornado.web
import json
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from ..models import HouseMember, House, User, EventHistory
from ..database import async_session_maker
from .base import BaseAPIHandler


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


class HouseMembersHandler(BaseAPIHandler):
    """Handler pour la gestion des membres d'une maison."""

    async def get(self, house_id):
        """Liste tous les membres d'une maison."""
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Not authenticated"})
            return

        house_id = int(house_id)
        user_id = current_user["id"]

        async with async_session_maker() as session:
            # Check that the user has access to this house
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
                    HouseMember.status == 'accepted'
                )
            )
            member_result = await session.execute(member_query)
            is_member = member_result.scalar_one_or_none() is not None

            if not is_owner and not is_member:
                self.set_status(403)
                self.write({"error": "Access denied"})
                return

            # Retrieve tous les membres
            query = select(HouseMember).where(
                HouseMember.house_id == house_id
            ).options(
                selectinload(HouseMember.user),
                selectinload(HouseMember.inviter)
            ).order_by(HouseMember.invited_at.desc())

            result = await session.execute(query)
            members = result.scalars().all()

            members_data = []
            for member in members:
                member_info = {
                    "id": member.id,
                    "user_id": member.user_id,
                    "username": member.user.username if member.user else None,
                    "email": member.user.email if member.user else None,
                    "role": member.role,
                    "status": member.status,
                    "invited_at": member.invited_at.isoformat(),
                    "accepted_at": member.accepted_at.isoformat()
                    if member.accepted_at else None,
                    "invited_by": member.invited_by,
                    "inviter_username": member.inviter.username
                    if member.inviter else None,
                }
                members_data.append(member_info)

            self.write({"members": members_data})

    async def post(self, house_id):
        """Inviter un nouveau membre à une maison."""
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Not authenticated"})
            return

        house_id = int(house_id)
        user_id = current_user["id"]

        try:
            data = json.loads(self.request.body)
            invited_username = data.get("username")
            role = data.get("role", "occupant")

            if not invited_username:
                self.set_status(400)
                self.write({"error": "Username required"})
                return

            if role not in ["administrateur", "occupant"]:
                self.set_status(400)
                self.write({"error": "Invalid role"})
                return

            async with async_session_maker() as session:
                # Check that la maison existe
                house = await session.get(House, house_id)
                if not house:
                    self.set_status(404)
                    self.write({"error": "House not found"})
                    return

                # Check that the inviter is owner or admin
                is_owner = house.user_id == user_id
                if not is_owner:
                    member_query = select(HouseMember).where(
                        and_(
                            HouseMember.house_id == house_id,
                            HouseMember.user_id == user_id,
                            HouseMember.role == 'administrateur',
                            HouseMember.status == 'accepted'
                        )
                    )
                    member_result = await session.execute(member_query)
                    is_admin = member_result.scalar_one_or_none() is not None
                    if not is_admin:
                        self.set_status(403)
                        self.write({
                            "error": "Only owners and administrators can invite"
                        })
                        return

                # Find the user to invite by username
                user_query = select(User).where(
                    User.username == invited_username
                )
                user_result = await session.execute(user_query)
                invited_user = user_result.scalar_one_or_none()

                if not invited_user:
                    self.set_status(404)
                    self.write({"error": "User not found"})
                    return
                
                # Empêcher de s'inviter soi-même
                if invited_user.id == user_id:
                    self.set_status(400)
                    self.write({"error": "Vous ne pouvez pas vous "
                               "inviter vous-même"})
                    return

                # Check if already member or invited
                existing_query = select(HouseMember).where(
                    and_(
                        HouseMember.house_id == house_id,
                        HouseMember.user_id == invited_user.id
                    )
                )
                existing_result = await session.execute(existing_query)
                existing = existing_result.scalar_one_or_none()

                if existing:
                    if existing.status == 'accepted':
                        self.set_status(400)
                        self.write({"error": "User already a member"})
                        return
                    elif existing.status == 'pending':
                        self.set_status(400)
                        self.write({"error": "Invitation already sent"})
                        return

                # Create l'invitation
                new_member = HouseMember(
                    house_id=house_id,
                    user_id=invited_user.id,
                    role=role,
                    invited_by=user_id,
                    status='pending'
                )
                session.add(new_member)

                # Enregistrer dans l'historique
                event = EventHistory(
                    house_id=house_id,
                    user_id=user_id,
                    event_type='member_action',
                    entity_type='member',
                    entity_id=invited_user.id,
                    description=f"Invitation envoyée à {invited_user.username}"
                    f" avec le rôle {role}",
                    event_metadata={
                        "action": "invite",
                        "invited_user_id": invited_user.id,
                        "role": role
                    },
                    ip_address=self.request.remote_ip
                )
                session.add(event)

                await session.commit()
                await session.refresh(new_member)

                self.set_status(201)
                self.write({
                    "message": "Invitation sent",
                    "member": {
                        "id": new_member.id,
                        "user_id": new_member.user_id,
                        "username": invited_user.username,
                        "role": new_member.role,
                        "status": new_member.status
                    }
                })

        except json.JSONDecodeError:
            self.set_status(400)
            self.write({"error": "Invalid JSON"})
        except Exception as e:
            self.set_status(500)
            self.write({"error": str(e)})


class HouseMemberDetailHandler(BaseAPIHandler):
    """Handler pour la gestion d'un membre spécifique."""

    async def patch(self, house_id, member_id):
        """Modifier le rôle d'un membre ou accepter/rejeter une invitation."""
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Not authenticated"})
            return

        house_id = int(house_id)
        member_id = int(member_id)
        user_id = current_user["id"]

        try:
            data = json.loads(self.request.body)
            new_role = data.get("role")
            new_status = data.get("status")

            async with async_session_maker() as session:
                # Retrieve le membre
                member = await session.get(HouseMember, member_id)
                if not member or member.house_id != house_id:
                    self.set_status(404)
                    self.write({"error": "Member not found"})
                    return

                house = await session.get(House, house_id)

                # Case 1: Accept/reject an invitation (invited user)
                if new_status and member.user_id == user_id:
                    if new_status not in ['accepted', 'rejected']:
                        self.set_status(400)
                        self.write({"error": "Invalid status"})
                        return

                    old_status = member.status
                    member.status = new_status
                    if new_status == 'accepted':
                        member.accepted_at = datetime.utcnow()

                    # Historique
                    event = EventHistory(
                        house_id=house_id,
                        user_id=user_id,
                        event_type='member_action',
                        entity_type='member',
                        entity_id=member.id,
                        description=f"Invitation {new_status}",
                        event_metadata={
                            "action": "invitation_response",
                            "old_status": old_status,
                            "new_status": new_status
                        },
                        ip_address=self.request.remote_ip
                    )
                    session.add(event)
                    await session.commit()

                    self.write({
                        "message": f"Invitation {new_status}",
                        "status": member.status
                    })
                    return

                # Case 2: Change role (admin or owner only)
                if new_role:
                    if new_role not in ["administrateur", "occupant"]:
                        self.set_status(400)
                        self.write({"error": "Invalid role"})
                        return

                    # Vérifier les permissions
                    is_owner = house.user_id == user_id
                    if not is_owner:
                        admin_query = select(HouseMember).where(
                            and_(
                                HouseMember.house_id == house_id,
                                HouseMember.user_id == user_id,
                                HouseMember.role == 'administrateur',
                                HouseMember.status == 'accepted'
                            )
                        )
                        admin_result = await session.execute(admin_query)
                        is_admin = admin_result.scalar_one_or_none() \
                            is not None
                        if not is_admin:
                            self.set_status(403)
                            self.write({
                                "error": "Permission denied"
                            })
                            return

                    old_role = member.role
                    member.role = new_role

                    # Historique
                    event = EventHistory(
                        house_id=house_id,
                        user_id=user_id,
                        event_type='member_action',
                        entity_type='member',
                        entity_id=member.id,
                        description=f"Rôle modifié de {old_role} "
                        f"à {new_role}",
                        event_metadata={
                            "action": "role_change",
                            "old_role": old_role,
                            "new_role": new_role,
                            "target_user_id": member.user_id
                        },
                        ip_address=self.request.remote_ip
                    )
                    session.add(event)
                    await session.commit()

                    self.write({
                        "message": "Role updated",
                        "role": member.role
                    })
                    return

                self.set_status(400)
                self.write({"error": "No modification specified"})

        except json.JSONDecodeError:
            self.set_status(400)
            self.write({"error": "Invalid JSON"})
        except Exception as e:
            self.set_status(500)
            self.write({"error": str(e)})

    async def delete(self, house_id, member_id):
        """Supprimer un membre d'une maison."""
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Not authenticated"})
            return

        house_id = int(house_id)
        member_id = int(member_id)
        user_id = current_user["id"]

        async with async_session_maker() as session:
            # Retrieve le membre
            member = await session.get(HouseMember, member_id)
            if not member or member.house_id != house_id:
                self.set_status(404)
                self.write({"error": "Member not found"})
                return

            house = await session.get(House, house_id)

            # Vérifier les permissions
            # Case 1: User removes themselves
            if member.user_id == user_id:
                # Empêcher le propriétaire de se retirer
                if house.user_id == user_id:
                    self.set_status(403)
                    self.write({
                        "error": "Owner cannot remove themselves"
                    })
                    return
            # Case 2: Admin or owner removes someone
            else:
                is_owner = house.user_id == user_id
                if not is_owner:
                    admin_query = select(HouseMember).where(
                        and_(
                            HouseMember.house_id == house_id,
                            HouseMember.user_id == user_id,
                            HouseMember.role == 'administrateur',
                            HouseMember.status == 'accepted'
                        )
                    )
                    admin_result = await session.execute(admin_query)
                    is_admin = admin_result.scalar_one_or_none() is not None
                    if not is_admin:
                        self.set_status(403)
                        self.write({"error": "Permission denied"})
                        return

            # Enregistrer dans l'historique avant suppression
            user_query = select(User).where(User.id == member.user_id)
            user_result = await session.execute(user_query)
            target_user = user_result.scalar_one_or_none()

            username = target_user.username if target_user else 'Inconnu'
            event = EventHistory(
                house_id=house_id,
                user_id=user_id,
                event_type='member_action',
                entity_type='member',
                entity_id=member.user_id,
                description=f"Membre {username} retiré",
                event_metadata={
                    "action": "remove",
                    "removed_user_id": member.user_id,
                    "was_role": member.role,
                    "self_removal": member.user_id == user_id
                },
                ip_address=self.request.remote_ip
            )
            session.add(event)

            await session.delete(member)
            await session.commit()

            self.write({"message": "Member removed"})


class MyInvitationsHandler(BaseAPIHandler):
    """Handler pour voir ses propres invitations."""

    async def get(self):
        """Liste toutes les invitations en attente de l'utilisateur."""
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Not authenticated"})
            return

        user_id = current_user["id"]

        async with async_session_maker() as session:
            query = select(HouseMember).where(
                and_(
                    HouseMember.user_id == user_id,
                    HouseMember.status == 'pending'
                )
            ).options(
                selectinload(HouseMember.house),
                selectinload(HouseMember.inviter)
            ).order_by(HouseMember.invited_at.desc())

            result = await session.execute(query)
            invitations = result.scalars().all()

            invitations_data = []
            for invitation in invitations:
                inv_info = {
                    "id": invitation.id,
                    "house_id": invitation.house_id,
                    "house_name": invitation.house.name
                    if invitation.house else None,
                    "role": invitation.role,
                    "invited_by": invitation.invited_by,
                    "inviter_username": invitation.inviter.username
                    if invitation.inviter else None,
                    "invited_at": invitation.invited_at.isoformat()
                }
                invitations_data.append(inv_info)

            self.write({"invitations": invitations_data})


class SearchUsersHandler(BaseAPIHandler):
    """Handler pour rechercher des utilisateurs à inviter."""

    async def get(self):
        """
        Recherche des utilisateurs par nom d'utilisateur.

        Query params:
        - q: terme de recherche (min 2 caractères)
        - limit: nombre max de résultats (défaut: 10, max: 50)
        """
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Not authenticated"})
            return

        search_term = self.get_argument("q", "").strip()
        limit = min(int(self.get_argument("limit", "10")), 50)

        if len(search_term) < 2:
            self.set_status(400)
            self.write({"error": "Minimum 2 characters required"})
            return

        async with async_session_maker() as session:
            # Rechercher les utilisateurs dont le username contient
            # le terme (insensible à la casse)
            query = select(User).where(
                User.username.ilike(f"%{search_term}%")
            ).limit(limit)

            result = await session.execute(query)
            users = result.scalars().all()

            users_data = []
            for user in users:
                # Ne pas inclure l'utilisateur lui-même
                if user.id != current_user["id"]:
                    users_data.append({
                        "id": user.id,
                        "username": user.username,
                        "profile_image": user.profile_image
                    })

            self.write({"users": users_data})


class SearchHousesHandler(BaseAPIHandler):
    """Handler pour rechercher des maisons publiquement."""

    async def get(self):
        """
        Recherche des maisons par nom.

        Query params:
        - q: terme de recherche (min 2 caractères)
        - limit: nombre max de résultats (défaut: 10, max: 50)
        """
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Not authenticated"})
            return

        search_term = self.get_argument("q", "").strip()
        limit = min(int(self.get_argument("limit", "10")), 50)
        user_id = current_user["id"]

        if len(search_term) < 2:
            self.set_status(400)
            self.write({"error": "Minimum 2 characters required"})
            return

        async with async_session_maker() as session:
            # Rechercher les maisons dont le nom contient le terme
            query = select(House).where(
                House.name.ilike(f"%{search_term}%")
            ).options(
                selectinload(House.user)
            ).limit(limit)

            result = await session.execute(query)
            houses = result.scalars().all()

            houses_data = []
            for house in houses:
                # Check if l'utilisateur a déjà une relation avec cette maison
                member_query = select(HouseMember).where(
                    and_(
                        HouseMember.house_id == house.id,
                        HouseMember.user_id == user_id
                    )
                )
                member_result = await session.execute(member_query)
                existing_member = member_result.scalar_one_or_none()

                is_owner = house.user_id == user_id
                relationship_status = None
                if is_owner:
                    relationship_status = "owner"
                elif existing_member:
                    relationship_status = existing_member.status

                houses_data.append({
                    "id": house.id,
                    "name": house.name,
                    "owner_id": house.user_id,
                    "owner_username": house.user.username if house.user else None,
                    "relationship_status": relationship_status
                })

            self.write({"houses": houses_data})


class RequestHouseAccessHandler(BaseAPIHandler):
    """Handler pour demander l'accès à une maison."""

    async def post(self, house_id):
        """Créer une demande d'accès à une maison."""
        current_user = self.get_current_user()
        if not current_user:
            self.set_status(401)
            self.write({"error": "Not authenticated"})
            return

        house_id = int(house_id)
        user_id = current_user["id"]

        try:
            data = json.loads(self.request.body)
            message = data.get("message", "")

            async with async_session_maker() as session:
                # Check that la maison existe
                house = await session.get(House, house_id)
                if not house:
                    self.set_status(404)
                    self.write({"error": "House not found"})
                    return

                # Empêcher le propriétaire de demander l'accès
                if house.user_id == user_id:
                    self.set_status(400)
                    self.write({"error": "You are already the owner of this house"})
                    return

                # Check if déjà membre ou demande existante
                existing_query = select(HouseMember).where(
                    and_(
                        HouseMember.house_id == house_id,
                        HouseMember.user_id == user_id
                    )
                )
                existing_result = await session.execute(existing_query)
                existing = existing_result.scalar_one_or_none()

                if existing:
                    if existing.status == 'accepted':
                        self.set_status(400)
                        self.write({"error": "You are already a member of this house"})
                        return
                    elif existing.status == 'pending':
                        self.set_status(400)
                        self.write({"error": "Request already pending"})
                        return
                    elif existing.status == 'rejected':
                        # Réinitialiser la demande
                        existing.status = 'pending'
                        existing.invited_at = datetime.utcnow()
                        existing.accepted_at = None

                        # Historique
                        event = EventHistory(
                            house_id=house_id,
                            user_id=user_id,
                            event_type='member_action',
                            entity_type='member',
                            entity_id=user_id,
                            description=f"{current_user['username']} re-requested access",
                            event_metadata={
                                "action": "access_request",
                                "message": message,
                                "is_renewal": True
                            },
                            ip_address=self.request.remote_ip
                        )
                        session.add(event)
                        await session.commit()

                        self.set_status(201)
                        self.write({
                            "message": "Access request renewed",
                            "request_id": existing.id
                        })
                        return

                # Create la demande d'accès (sans invited_by car auto-demande)
                new_request = HouseMember(
                    house_id=house_id,
                    user_id=user_id,
                    role='occupant',  # Par défaut occupant
                    invited_by=None,  # Aucun inviteur (auto-demande)
                    status='pending'
                )
                session.add(new_request)

                # Historique
                event = EventHistory(
                    house_id=house_id,
                    user_id=user_id,
                    event_type='member_action',
                    entity_type='member',
                    entity_id=user_id,
                    description=f"{current_user['username']} requested access",
                    event_metadata={
                        "action": "access_request",
                        "message": message
                    },
                    ip_address=self.request.remote_ip
                )
                session.add(event)

                await session.commit()
                await session.refresh(new_request)

                self.set_status(201)
                self.write({
                    "message": "Access request sent",
                    "request_id": new_request.id
                })

        except json.JSONDecodeError:
            self.set_status(400)
            self.write({"error": "Invalid JSON"})
        except Exception as e:
            self.set_status(500)
            self.write({"error": str(e)})
