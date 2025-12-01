/**
 * Module de gestion WebSocket pour les mises à jour en temps réel
 * des capteurs et équipements
 */

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;
const RECONNECT_BASE_DELAY = 1000; // 1 seconde

/**
 * Établit la connexion WebSocket avec le serveur
 */
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/realtime`;
    
    console.log('[WebSocket] Tentative de connexion...', wsUrl);
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = handleOpen;
        ws.onmessage = handleMessage;
        ws.onerror = handleError;
        ws.onclose = handleClose;
    } catch (error) {
        console.error('[WebSocket] Erreur de connexion:', error);
        scheduleReconnect();
    }
}

/**
 * Gère l'ouverture de la connexion WebSocket
 */
function handleOpen() {
    console.log('[WebSocket] Connexion établie');
    reconnectAttempts = 0;
    updateConnectionStatus(true);
    
    // Envoyer un ping toutes les 30 secondes pour maintenir la connexion
    if (ws.pingInterval) {
        clearInterval(ws.pingInterval);
    }
    ws.pingInterval = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
        }
    }, 30000);
}

/**
 * Gère les messages reçus du serveur
 */
function handleMessage(event) {
    try {
        const message = JSON.parse(event.data);
        console.log('[WebSocket] Message reçu:', message);
        
        // Filtrer par house_id si présent (pour capteurs et équipements)
        if (message.house_id && window.currentHouseId) {
            if (message.house_id !== window.currentHouseId) {
                console.log('[WebSocket] Message ignoré (autre maison):', 
                    message.house_id, 'vs', window.currentHouseId);
                return;
            }
        }
        
        switch (message.type) {
            case 'sensor_update':
                updateSensorInUI(message.data);
                break;
            case 'equipment_update':
                updateEquipmentInUI(message.data);
                break;
            case 'grid_update':
                // Mise à jour du plan de la maison
                if (message.house_id && window.currentHouseId && 
                    message.house_id === window.currentHouseId) {
                    updateGridInUI(message.data);
                }
                break;
            case 'equipment_crud':
                // Ajout/modification/suppression d'équipement
                if (message.house_id && window.currentHouseId && 
                    message.house_id === window.currentHouseId) {
                    handleEquipmentCRUD(message.action, message.data);
                }
                break;
            case 'sensor_crud':
                // Ajout/modification/suppression de capteur
                if (message.house_id && window.currentHouseId && 
                    message.house_id === window.currentHouseId) {
                    handleSensorCRUD(message.action, message.data);
                }
                break;
            case 'room_crud':
                // Ajout/modification/suppression de pièce
                if (message.house_id && window.currentHouseId && 
                    message.house_id === window.currentHouseId) {
                    handleRoomCRUD(message.action, message.data);
                }
                break;
            case 'automation_rule_crud':
                // Ajout/modification/suppression de règle d'automatisation
                if (message.house_id && window.currentHouseId && 
                    message.house_id === window.currentHouseId) {
                    handleAutomationRuleCRUD(message.action, message.data);
                }
                break;
            case 'user_position_changed':
            case 'user_position_deactivated':
                // Filtrer par house_id pour les positions
                if (message.house_id && window.currentHouseId && 
                    message.house_id !== window.currentHouseId) {
                    return;
                }
                if (typeof handlePositionUpdate === 'function') {
                    handlePositionUpdate(message);
                }
                break;
            case 'pong':
                // Réponse au ping, la connexion est active
                break;
            default:
                console.warn('[WebSocket] Type de message inconnu:', message.type);
        }
    } catch (error) {
        console.error('[WebSocket] Erreur de traitement du message:', error);
    }
}

/**
 * Gère les erreurs WebSocket
 */
function handleError(error) {
    console.error('[WebSocket] Erreur:', error);
    updateConnectionStatus(false);
}

/**
 * Gère la fermeture de la connexion
 */
function handleClose(event) {
    console.log('[WebSocket] Connexion fermée', event.code, event.reason);
    updateConnectionStatus(false);
    
    if (ws.pingInterval) {
        clearInterval(ws.pingInterval);
    }
    
    // Reconnexion automatique sauf si c'est une déconnexion volontaire
    if (event.code !== 1000) {
        scheduleReconnect();
    }
}

/**
 * Planifie une tentative de reconnexion avec backoff exponentiel
 */
function scheduleReconnect() {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.error('[WebSocket] Nombre maximal de tentatives de reconnexion atteint');
        showReconnectionError();
        return;
    }
    
    const delay = RECONNECT_BASE_DELAY * Math.pow(2, reconnectAttempts);
    reconnectAttempts++;
    
    console.log(`[WebSocket] Reconnexion dans ${delay}ms (tentative ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
    
    setTimeout(() => {
        connectWebSocket();
    }, delay);
}

/**
 * Met à jour l'indicateur visuel de statut de connexion
 */
function updateConnectionStatus(connected) {
    const indicator = document.getElementById('ws-status-indicator');
    if (indicator) {
        if (connected) {
            indicator.style.backgroundColor = '#4caf50';
            indicator.title = 'Connecté en temps réel';
        } else {
            indicator.style.backgroundColor = '#f44336';
            indicator.title = 'Déconnecté';
        }
    }
}

/**
 * Affiche un message d'erreur si la reconnexion échoue
 */
function showReconnectionError() {
    const message = document.createElement('div');
    message.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #f44336;
        color: white;
        padding: 15px 20px;
        border-radius: 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        z-index: 10000;
    `;
    message.textContent = 'Impossible de se connecter au serveur en temps réel. Rechargez la page.';
    document.body.appendChild(message);
}

/**
 * Met à jour l'affichage d'un capteur dans l'interface
 */
function updateSensorInUI(data) {
    console.log('📡 [Realtime] Message WebSocket reçu - Capteur:', data);
    
    // Mettre à jour le tableau global des capteurs (si accessible)
    if (typeof sensors !== 'undefined' && Array.isArray(sensors)) {
        const sensorIndex = sensors.findIndex(s => s.id === data.id);
        if (sensorIndex !== -1) {
            sensors[sensorIndex].value = data.value;
            if (data.is_active !== undefined) {
                sensors[sensorIndex].is_active = data.is_active;
            }
        }
    }
    
    // Mettre à jour dans la grille de la maison
    const gridCell = document.querySelector(`[data-sensor-id="${data.id}"]`);
    if (gridCell || typeof refreshSensorInGrid === 'function') {
        // Rafraîchir l'affichage du capteur dans la grille
        // Cette fonction doit être implémentée dans house.js
        if (typeof refreshSensorInGrid === 'function') {
            // Formater les données au bon format attendu par refreshSensorInGrid
            refreshSensorInGrid({
                sensor_id: data.id,
                value: data.value,
                is_active: data.is_active
            });
        }
    }
    
    // Mettre à jour dans la liste des capteurs (dashboard)
    const sensorCard = document.getElementById(`sensor-${data.id}`);
    if (sensorCard) {
        const valueElement = sensorCard.querySelector('.sensor-value');
        if (valueElement) {
            valueElement.textContent = data.value;
            // Animation de mise à jour
            sensorCard.style.animation = 'pulse 0.5s';
            setTimeout(() => {
                sensorCard.style.animation = '';
            }, 500);
        }
        
        // Mettre à jour le badge actif/inactif si nécessaire
        if (data.is_active !== undefined) {
            const statusBadge = sensorCard.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.className = `status-badge ${data.is_active ? 'status-active' : 'status-inactive'}`;
                statusBadge.textContent = data.is_active ? 'Actif' : 'Inactif';
            }
        }
    }
}

/**
 * Met à jour l'affichage d'un équipement dans l'interface
 */
function updateEquipmentInUI(data) {
    console.log('[WebSocket] Mise à jour de l\'équipement:', data);
    
    // TOUJOURS mettre à jour l'équipement dans le tableau global
    // Cette fonction doit être appelée inconditionnellement
    if (typeof refreshEquipmentInGrid === 'function') {
        console.log('[WebSocket] Appel de refreshEquipmentInGrid avec:', data);
        refreshEquipmentInGrid(data);
    } else {
        console.warn('[WebSocket] refreshEquipmentInGrid n\'est pas définie');
    }
    
    // Mettre à jour dans la liste des équipements (si présente)
    const equipmentCard = document.getElementById(`equipment-${data.id}`);
    if (equipmentCard) {
        // Mettre à jour l'état affiché
        const stateElement = equipmentCard.querySelector('.equipment-state');
        if (stateElement) {
            stateElement.textContent = data.state;
            
            // Mettre à jour le style en fonction de l'état
            updateEquipmentCardStyle(equipmentCard, data);
            
            // Animation de mise à jour
            equipmentCard.style.animation = 'pulse 0.5s';
            setTimeout(() => {
                equipmentCard.style.animation = '';
            }, 500);
        }
    }
}

/**
 * Met à jour le style de la carte d'équipement en fonction de l'état
 */
function updateEquipmentCardStyle(card, data) {
    // Réinitialiser les styles
    card.style.backgroundColor = '';
    card.style.borderColor = '';
    
    // Appliquer les styles selon le type et l'état
    if (data.type === 'shutter') {
        if (data.state === 'open') {
            card.style.backgroundColor = '#e8f5e9';
            card.style.borderColor = '#4caf50';
        } else {
            card.style.backgroundColor = '#ffe6e6';
            card.style.borderColor = '#dc3545';
        }
    } else if (data.type === 'door') {
        if (data.state === 'open') {
            card.style.backgroundColor = '#e8f5e9';
            card.style.borderColor = '#4caf50';
        } else {
            card.style.backgroundColor = '#ffe6e6';
            card.style.borderColor = '#dc3545';
        }
    } else if (data.type === 'light') {
        if (data.state === 'on') {
            card.style.backgroundColor = '#fff9e6';
            card.style.borderColor = '#ffc107';
        } else {
            card.style.backgroundColor = '#f5f5f5';
        }
    } else if (data.type === 'sound_system') {
        if (data.state === 'on') {
            card.style.backgroundColor = '#e3f2fd';
            card.style.borderColor = '#2196f3';
        } else {
            card.style.backgroundColor = '#f5f5f5';
        }
    }
}

/**
 * Met à jour la grille (plan) de la maison en temps réel
 */
function updateGridInUI(data) {
    console.log('[WebSocket] Mise à jour du plan de la maison:', data);
    
    // Mettre à jour l'objet house global avec la nouvelle grille
    if (typeof house !== 'undefined' && house) {
        house.grid = data.grid;
        console.log('[WebSocket] Grille mise à jour dans l\'objet house');
        
        // Rafraîchir l'affichage du plan
        if (typeof displayHouseGrid === 'function') {
            displayHouseGrid();
            console.log('[WebSocket] Plan de la maison rafraîchi');
            
            // Afficher une notification discrète
            showGridUpdateNotification();
        }
    }
}

/**
 * Affiche une notification discrète de mise à jour du plan
 */
function showGridUpdateNotification() {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #4caf50;
        color: white;
        padding: 12px 20px;
        border-radius: 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        z-index: 10000;
        font-size: 14px;
        animation: slideIn 0.3s ease-out;
    `;
    notification.innerHTML = 'Plan mis à jour';
    document.body.appendChild(notification);
    
    // Retirer après 3 secondes
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

/**
 * Gère les événements CRUD d'équipements
 */
function handleEquipmentCRUD(action, data) {
    console.log('[WebSocket] Equipment CRUD:', action, data);
    
    if (action === 'create') {
        // Recharger la liste des équipements
        if (typeof loadEquipments === 'function') {
            loadEquipments().then(() => {
                displayHouseGrid();
                showNotification('Nouvel équipement ajouté', '#2196f3');
            });
        }
    } else if (action === 'update') {
        // Recharger la liste des équipements pour mise à jour du nom
        if (typeof loadEquipments === 'function') {
            loadEquipments().then(() => {
                displayHouseGrid();
                showNotification('Équipement modifié', '#2196f3');
            });
        }
    } else if (action === 'delete') {
        // Recharger la liste des équipements
        if (typeof loadEquipments === 'function') {
            loadEquipments().then(() => {
                displayHouseGrid();
                showNotification('Équipement supprimé', '#ff9800');
            });
        }
    }
}

/**
 * Gère les événements CRUD de capteurs
 */
function handleSensorCRUD(action, data) {
    console.log('[WebSocket] Sensor CRUD:', action, data);
    
    if (action === 'create') {
        // Recharger la liste des capteurs
        if (typeof loadSensors === 'function') {
            loadSensors().then(() => {
                displayHouseGrid();
                showNotification('Nouveau capteur ajouté', '#4caf50');
            });
        }
    } else if (action === 'update') {
        // Recharger la liste des capteurs pour mise à jour du nom/unité
        if (typeof loadSensors === 'function') {
            loadSensors().then(() => {
                displayHouseGrid();
                showNotification('Capteur modifié', '#4caf50');
            });
        }
    } else if (action === 'delete') {
        // Recharger la liste des capteurs
        if (typeof loadSensors === 'function') {
            loadSensors().then(() => {
                displayHouseGrid();
                showNotification('Capteur supprimé', '#ff9800');
            });
        }
    }
}

/**
 * Gère les événements CRUD de pièces
 */
function handleRoomCRUD(action, data) {
    console.log('[WebSocket] Room CRUD:', action, data);
    
    if (action === 'create') {
        // Recharger toute la maison pour avoir les nouvelles pièces
        if (typeof loadHouse === 'function') {
            loadHouse().then(() => {
                showNotification('Nouvelle pièce ajoutée', '#9c27b0');
            });
        }
    } else if (action === 'update') {
        // Recharger toute la maison pour la mise à jour du nom
        if (typeof loadHouse === 'function') {
            loadHouse().then(() => {
                showNotification('Pièce modifiée', '#9c27b0');
            });
        }
    } else if (action === 'delete') {
        // Recharger toute la maison
        if (typeof loadHouse === 'function') {
            loadHouse().then(() => {
                showNotification('Pièce supprimée', '#ff9800');
            });
        }
    }
}

/**
 * Gère les événements CRUD de règles d'automatisation
 */
function handleAutomationRuleCRUD(action, data) {
    console.log('[WebSocket] Automation Rule CRUD:', action, data);
    
    if (action === 'create') {
        // Recharger les règles d'automatisation
        if (typeof loadAutomationRules === 'function') {
            loadAutomationRules().then(() => {
                showNotification('Nouvelle règle d\'automatisation ajoutée', '#673ab7');
            });
        }
    } else if (action === 'update') {
        // Recharger les règles d'automatisation
        if (typeof loadAutomationRules === 'function') {
            loadAutomationRules().then(() => {
                showNotification('Règle d\'automatisation modifiée', '#673ab7');
            });
        }
    } else if (action === 'delete') {
        // Recharger les règles d'automatisation
        if (typeof loadAutomationRules === 'function') {
            loadAutomationRules().then(() => {
                showNotification('Règle d\'automatisation supprimée', '#ff9800');
            });
        }
    }
}

/**
 * Affiche une notification avec couleur personnalisée
 */
function showNotification(message, color) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: ${color};
        color: white;
        padding: 12px 20px;
        border-radius: 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        z-index: 10000;
        font-size: 14px;
        animation: slideIn 0.3s ease-out;
    `;
    notification.innerHTML = message;
    document.body.appendChild(notification);
    
    // Retirer après 3 secondes
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

/**
 * Ferme proprement la connexion WebSocket
 */
function disconnectWebSocket() {
    if (ws) {
        if (ws.pingInterval) {
            clearInterval(ws.pingInterval);
        }
        ws.close(1000, 'Client disconnect');
        ws = null;
    }
}

// Connexion automatique au chargement de la page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', connectWebSocket);
} else {
    connectWebSocket();
}

// Déconnexion propre à la fermeture de la page
window.addEventListener('beforeunload', disconnectWebSocket);

// CSS pour les animations
const style = document.createElement('style');
style.textContent = `
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}
@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
@keyframes slideOut {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(400px);
        opacity: 0;
    }
}
`;
document.head.appendChild(style);
