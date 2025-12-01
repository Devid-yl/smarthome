"""
WebSocket handler pour la mise à jour en temps réel
"""

import json
import tornado.websocket
from typing import Set


class RealtimeHandler(tornado.websocket.WebSocketHandler):
    """
    WebSocket pour les mises à jour en temps réel des capteurs et équipements
    """

    # Set of all connected clients
    clients: Set["RealtimeHandler"] = set()

    def check_origin(self, origin):
        """Autoriser toutes les origines (à restreindre en production)"""
        return True

    def get_current_user(self):
        """Récupérer l'utilisateur authentifié depuis le cookie"""
        uid = self.get_secure_cookie("uid")
        return int(uid) if uid else None

    def open(self):
        """Connexion WebSocket établie"""
        user_id = self.get_current_user()
        if not user_id:
            self.close(code=401, reason="Not authenticated")
            return

        self.user_id = user_id
        RealtimeHandler.clients.add(self)
        print(
            f"[WebSocket] Client connecté (user_id={user_id}). "
            f"Total clients: {len(RealtimeHandler.clients)}"
        )

    def on_message(self, message):
        """Message reçu du client (optionnel, pour ping/pong)"""
        try:
            data = json.loads(message)
            if data.get("type") == "ping":
                self.write_message(json.dumps({"type": "pong"}))
        except json.JSONDecodeError:
            pass

    def on_close(self):
        """Connexion fermée"""
        RealtimeHandler.clients.discard(self)
        print(
            f"[WebSocket] Client déconnecté. "
            f"Total clients: {len(RealtimeHandler.clients)}"
        )

    @classmethod
    def broadcast_sensor_update(
        cls, sensor_id: int, value: float, is_active: bool, house_id: int | None = None
    ):
        """
        Diffuser une mise à jour de capteur à tous les clients connectés
        """
        message = json.dumps(
            {
                "type": "sensor_update",
                "house_id": house_id,
                "data": {"id": sensor_id, "value": value, "is_active": is_active},
            }
        )

        print(
            f"[WebSocket] Broadcasting sensor update: "
            f"sensor_id={sensor_id}, value={value}"
        )
        dead_clients = set()

        for client in cls.clients:
            try:
                client.write_message(message)
            except Exception as e:
                print(f"[WebSocket] Error sending to client: {e}")
                dead_clients.add(client)

        # Nettoyer les clients morts
        for client in dead_clients:
            cls.clients.discard(client)

    @classmethod
    def broadcast_equipment_update(
        cls,
        equipment_id: int,
        equipment_type: str,
        state: str,
        is_active: bool,
        house_id: int | None = None,
    ):
        """
        Diffuser une mise à jour d'équipement à tous les clients connectés
        """
        message = json.dumps(
            {
                "type": "equipment_update",
                "house_id": house_id,
                "data": {
                    "id": equipment_id,
                    "type": equipment_type,
                    "state": state,
                    "is_active": is_active,
                },
            }
        )

        print(
            f"[WebSocket] Broadcasting equipment update: "
            f"equipment_id={equipment_id}, state={state}"
        )
        print(f"[WebSocket] Envoi à {len(cls.clients)} client(s)")
        dead_clients = set()
        sent_count = 0

        for client in cls.clients:
            try:
                client.write_message(message)
                sent_count += 1
                print(
                    f"[WebSocket] Message envoyé au client (user_id={client.user_id})"
                )
            except Exception as e:
                print(f"[WebSocket] Error sending to client: {e}")
                dead_clients.add(client)

        print(
            f"[WebSocket] Broadcast terminé: "
            f"{sent_count}/{len(cls.clients)} messages envoyés"
        )

        # Nettoyer les clients morts
        for client in dead_clients:
            cls.clients.discard(client)

    @classmethod
    def broadcast_grid_update(cls, house_id: int, grid: list):
        """
        Diffuser une mise à jour de la grille (plan) à tous les clients connectés
        """
        message = json.dumps(
            {
                "type": "grid_update",
                "house_id": house_id,
                "data": {"grid": grid},
            }
        )

        print(
            f"[WebSocket] Broadcasting grid update: house_id={house_id}"
        )
        dead_clients = set()

        for client in cls.clients:
            try:
                client.write_message(message)
            except Exception as e:
                print(f"[WebSocket] Error sending to client: {e}")
                dead_clients.add(client)

        # Nettoyer les clients morts
        for client in dead_clients:
            cls.clients.discard(client)

    @classmethod
    def broadcast_equipment_crud(cls, action: str, equipment_data: dict, house_id: int):
        """
        Diffuser un événement CRUD d'équipement (create/delete) à tous les clients
        """
        message = json.dumps(
            {
                "type": "equipment_crud",
                "house_id": house_id,
                "action": action,  # 'create' or 'delete'
                "data": equipment_data,
            }
        )

        print(
            f"[WebSocket] Broadcasting equipment {action}: equipment_id={equipment_data.get('id')}"
        )
        dead_clients = set()

        for client in cls.clients:
            try:
                client.write_message(message)
            except Exception as e:
                print(f"[WebSocket] Error sending to client: {e}")
                dead_clients.add(client)

        # Nettoyer les clients morts
        for client in dead_clients:
            cls.clients.discard(client)

    @classmethod
    def broadcast_sensor_crud(cls, action: str, sensor_data: dict, house_id: int):
        """
        Diffuser un événement CRUD de capteur (create/delete) à tous les clients
        """
        message = json.dumps(
            {
                "type": "sensor_crud",
                "house_id": house_id,
                "action": action,  # 'create' or 'delete'
                "data": sensor_data,
            }
        )

        print(
            f"[WebSocket] Broadcasting sensor {action}: sensor_id={sensor_data.get('id')}"
        )
        dead_clients = set()

        for client in cls.clients:
            try:
                client.write_message(message)
            except Exception as e:
                print(f"[WebSocket] Error sending to client: {e}")
                dead_clients.add(client)

        # Nettoyer les clients morts
        for client in dead_clients:
            cls.clients.discard(client)

    @classmethod
    def broadcast_room_crud(cls, action: str, room_data: dict, house_id: int):
        """
        Diffuser un événement CRUD de pièce (create/update/delete) à tous les clients
        """
        message = json.dumps(
            {
                "type": "room_crud",
                "house_id": house_id,
                "action": action,  # 'create', 'update' or 'delete'
                "data": room_data,
            }
        )

        print(
            f"[WebSocket] Broadcasting room {action}: room_id={room_data.get('id')}"
        )
        dead_clients = set()

        for client in cls.clients:
            try:
                client.write_message(message)
            except Exception as e:
                print(f"[WebSocket] Error sending to client: {e}")
                dead_clients.add(client)

        # Nettoyer les clients morts
        for client in dead_clients:
            cls.clients.discard(client)

    @classmethod
    def broadcast_automation_rule_crud(cls, action: str, rule_data: dict, house_id: int):
        """
        Diffuser un événement CRUD de règle d'automatisation (create/update/delete) à tous les clients
        """
        message = json.dumps(
            {
                "type": "automation_rule_crud",
                "house_id": house_id,
                "action": action,  # 'create', 'update' or 'delete'
                "data": rule_data,
            }
        )

        print(
            f"[WebSocket] Broadcasting automation rule {action}: rule_id={rule_data.get('id')}"
        )
        dead_clients = set()

        for client in cls.clients:
            try:
                client.write_message(message)
            except Exception as e:
                print(f"[WebSocket] Error sending to client: {e}")
                dead_clients.add(client)

        # Nettoyer les clients morts
        for client in dead_clients:
            cls.clients.discard(client)

    @classmethod
    def broadcast_access_request(cls, house_id: int, request_data: dict):
        """
        Diffuser une nouvelle demande d'accès aux propriétaires/admins
        """
        message = json.dumps(
            {
                "type": "access_request",
                "house_id": house_id,
                "data": request_data,
            }
        )

        print(
            f"[WebSocket] Broadcasting access request: house_id={house_id}, user={request_data.get('username')}"
        )
        dead_clients = set()

        for client in cls.clients:
            try:
                client.write_message(message)
            except Exception as e:
                print(f"[WebSocket] Error sending to client: {e}")
                dead_clients.add(client)

        # Nettoyer les clients morts
        for client in dead_clients:
            cls.clients.discard(client)
