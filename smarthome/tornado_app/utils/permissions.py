"""Module de gestion des permissions pour les maisons et équipements."""
from sqlalchemy import select, and_
from ..models import House, HouseMember


class PermissionLevel:
    """Niveaux de permission."""
    NONE = 0
    VIEW = 1
    CONTROL = 2
    MANAGE = 3
    OWNER = 4


async def get_user_house_permission(session, user_id, house_id):
    """
    Retourne le niveau de permission d'un utilisateur sur une maison.

    Returns:
        PermissionLevel: Le niveau de permission le plus élevé
    """
    # Vérifier si propriétaire
    house = await session.get(House, house_id)
    if not house:
        return PermissionLevel.NONE

    if house.user_id == user_id:
        return PermissionLevel.OWNER

    # Vérifier le statut de membre
    query = select(HouseMember).where(
        and_(
            HouseMember.house_id == house_id,
            HouseMember.user_id == user_id,
            HouseMember.status == 'accepted'
        )
    )
    result = await session.execute(query)
    member = result.scalar_one_or_none()

    if not member:
        return PermissionLevel.NONE

    # Mapper les rôles aux permissions
    if member.role == 'administrateur':
        return PermissionLevel.MANAGE
    elif member.role == 'occupant':
        return PermissionLevel.CONTROL

    return PermissionLevel.NONE


async def can_view_house(session, user_id, house_id):
    """Vérifie si l'utilisateur peut voir la maison."""
    permission = await get_user_house_permission(session, user_id, house_id)
    return permission >= PermissionLevel.VIEW


async def can_control_equipment(session, user_id, house_id, equipment=None):
    """
    Vérifie si l'utilisateur peut contrôler un équipement.
    
    Args:
        session: Session de base de données
        user_id: ID de l'utilisateur
        house_id: ID de la maison
        equipment: Objet Equipment optionnel pour vérifier allowed_roles
    
    Returns:
        bool: True si l'utilisateur peut contrôler l'équipement
    """
    permission = await get_user_house_permission(session, user_id, house_id)
    
    # Pas de permission de base
    if permission < PermissionLevel.CONTROL:
        return False
    
    # Le propriétaire peut TOUJOURS contrôler tous les équipements
    if permission == PermissionLevel.OWNER:
        return True
    
    # Si pas d'équipement spécifique, vérifier juste la permission générale
    if not equipment:
        return True
    
    # Vérifier les rôles autorisés pour cet équipement
    if equipment.allowed_roles:
        user_role = await get_user_role_in_house(session, user_id, house_id)
        # Si allowed_roles est défini et non vide, vérifier le rôle
        return user_role in equipment.allowed_roles
    
    # Si allowed_roles est None ou vide, tous les rôles avec CONTROL+ peuvent
    return True


async def can_manage_house(session, user_id, house_id):
    """
    Vérifie si l'utilisateur peut gérer la maison
    (éditer, ajouter/supprimer pièces, etc.).
    """
    permission = await get_user_house_permission(session, user_id, house_id)
    return permission >= PermissionLevel.MANAGE


async def is_house_owner(session, user_id, house_id):
    """Vérifie si l'utilisateur est propriétaire de la maison."""
    permission = await get_user_house_permission(session, user_id, house_id)
    return permission == PermissionLevel.OWNER


async def get_user_role_in_house(session, user_id, house_id):
    """
    Retourne le rôle de l'utilisateur dans une maison.

    Returns:
        str: 'proprietaire', 'administrateur', 'occupant', ou None
    """
    house = await session.get(House, house_id)
    if not house:
        return None

    if house.user_id == user_id:
        return 'proprietaire'

    query = select(HouseMember).where(
        and_(
            HouseMember.house_id == house_id,
            HouseMember.user_id == user_id,
            HouseMember.status == 'accepted'
        )
    )
    result = await session.execute(query)
    member = result.scalar_one_or_none()

    if member:
        return member.role

    return None
