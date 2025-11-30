// house.js - Logique pour la page de détails d'une maison

let houseId = null;
let house = null;

// Exposer houseId globalement pour le filtrage WebSocket
Object.defineProperty(window, 'currentHouseId', {
    get: () => houseId ? parseInt(houseId) : null
});
let userRole = null;
let rooms = [];
let sensors = [];
let equipments = [];
let automationRules = [];

// Exposer sensors globalement pour que weather.js puisse y accéder
window.sensors = sensors;

// Movement simulation state
let movementMode = false;
let userPositions = new Map(); // Map<user_id, {x, y, username}>
let myPosition = null;

// ==================== GRID LAYERS UTILITIES ====================
function isLegacyGrid(grid) {
    return grid && grid[0] && typeof grid[0][0] === 'number';
}

function getCellBase(cell) {
    return typeof cell === 'number' ? cell : (cell.base || 0);
}

function getCellSensors(cell) {
    return typeof cell === 'number' ? [] : (cell.sensors || []);
}

function getCellEquipments(cell) {
    return typeof cell === 'number' ? [] : (cell.equipments || []);
}

// Initialisation
async function init() {
    const params = new URLSearchParams(window.location.search);
    houseId = params.get('id');
    
    if (!houseId) {
        alert('ID de maison manquant');
        goBack();
        return;
    }
    
    // Attacher les gestionnaires d'événements aux boutons
    const editBtn = document.getElementById('edit-house-btn');
    const deleteBtn = document.getElementById('delete-house-btn');
    const editInteriorBtn = document.getElementById('edit-interior-btn');
    const editHouseForm = document.getElementById('edit-house-form');
    
    // Les boutons n'existent plus dans le DOM, les fonctions sont appelées depuis le menu
    // if (editBtn && deleteBtn) {
    //     console.log('Attaching event listeners to buttons');
    //     editBtn.addEventListener('click', editHouse);
    //     deleteBtn.addEventListener('click', deleteHouse);
    // } else {
    //     console.error('Buttons not found:', { editBtn, deleteBtn });
    // }
    
    if (editInteriorBtn) {
        editInteriorBtn.addEventListener('click', openGridEditor);
    }
    
    if (editHouseForm) {
        editHouseForm.addEventListener('submit', submitEditHouse);
    }
    
    // Afficher immédiatement le cache météo si disponible
    if (typeof loadWeatherFromCache === 'function') {
        loadWeatherFromCache(houseId);
    }
    
    await loadHouse();
    await loadSensors(); // Charger les capteurs AVANT la météo
    await loadEquipments();
    await loadAutomationRules();
    await loadUserPositions(); // Always load positions to see other users
    
    // Rafraîchir le plan après le chargement des pièces
    displayHouseGrid();
    
    // Charger la météo APRÈS les capteurs pour pouvoir synchroniser
    if (typeof loadWeather === 'function') {
        await loadWeather(houseId);
    }
    
    // Initialiser le widget météo (interval de rafraîchissement)
    if (typeof initWeather === 'function') {
        initWeather(houseId);
    }
    
    // Vérifier si on revient de l'éditeur de grille
    checkGridEditorReturn();
}

// Vérifier si on revient de l'éditeur avec des données de grille
function checkGridEditorReturn() {
    const params = new URLSearchParams(window.location.search);
    const gridData = params.get('grid');
    
    if (gridData) {
        // Stocker temporairement les données de grille
        tempGridData = decodeURIComponent(gridData);
        // Nettoyer l'URL
        window.history.replaceState({}, '', `/app/house.html?id=${houseId}`);
        // Afficher un message à l'utilisateur
        alert('Plan mis à jour !');
    }
}

// Charger les détails de la maison
async function loadHouse() {
    try {
        const response = await fetch(`/api/houses/${houseId}`);
        if (response.ok) {
            house = await response.json();
            userRole = house.user_role;
            document.getElementById('house-name').textContent = house.name;
            document.getElementById('house-title').textContent = house.name;
            document.getElementById('house-info').textContent = 
                `${house.address || 'Pas d\'adresse'} | ${house.length * house.width} m²`;
            
            // Charger les pièces
            if (house.rooms) {
                rooms = house.rooms;
            }
            
            // Masquer les éléments selon les permissions
            applyPermissions();
        } else {
            alert('Maison introuvable');
            goBack();
        }
    } catch (error) {
        alert('Erreur de chargement');
        goBack();
    }
}

// Appliquer les permissions d'affichage selon le rôle
function applyPermissions() {
    const isAdmin = userRole === 'proprietaire' || userRole === 'admin';
    
    // Masquer les boutons de modification/suppression pour les non-admin
    const editBtn = document.getElementById('edit-house-btn');
    const deleteBtn = document.getElementById('delete-house-btn');
    const editInteriorBtn = document.getElementById('edit-interior-btn');
    const membersBtn = document.getElementById('members-btn');
    const historyBtn = document.getElementById('history-btn');
    const headerMenu = document.querySelector('.header-menu-btn');
    
    if (!isAdmin) {
        if (editBtn) editBtn.style.display = 'none';
        if (deleteBtn) deleteBtn.style.display = 'none';
        if (editInteriorBtn) editInteriorBtn.style.display = 'none';
        if (membersBtn) membersBtn.style.display = 'none';
        if (historyBtn) historyBtn.style.display = 'none';
        if (headerMenu) headerMenu.style.display = 'none';
        
        // Masquer les onglets Capteurs et Automatisation
        const sensorsTab = document.querySelector('.tab[onclick*="sensors"]');
        const automationTab = document.querySelector('.tab[onclick*="automation"]');
        const sensorsContent = document.getElementById('tab-sensors');
        const automationContent = document.getElementById('tab-automation');
        
        if (sensorsTab) sensorsTab.style.display = 'none';
        if (automationTab) automationTab.style.display = 'none';
        if (sensorsContent) sensorsContent.style.display = 'none';
        if (automationContent) automationContent.style.display = 'none';
        
        // Masquer les boutons d'ajout dans l'onglet équipements
        const addEquipmentBtn = document.getElementById('add-equipment-btn');
        if (addEquipmentBtn) addEquipmentBtn.style.display = 'none';
        
        // Activer automatiquement l'onglet Équipements
        const equipmentsTab = document.querySelector('.tab[onclick*="equipments"]');
        if (equipmentsTab) {
            equipmentsTab.classList.add('active');
        }
        const equipmentsContent = document.getElementById('tab-equipments');
        if (equipmentsContent) {
            equipmentsContent.classList.add('active');
        }
    } else {
        // Pour les admin, activer l'onglet équipements par défaut aussi
        const equipmentsTab = document.querySelector('.tab[onclick*="equipments"]');
        if (equipmentsTab) {
            equipmentsTab.classList.add('active');
        }
        const equipmentsContent = document.getElementById('tab-equipments');
        if (equipmentsContent) {
            equipmentsContent.classList.add('active');
        }
    }
}

// Afficher le plan de la maison (grille interactive avec icônes)
function displayHouseGrid() {
    console.log('[House] displayHouseGrid() appelée, nombre d\'équipements:', equipments.length);
    const gridContainer = document.getElementById('house-grid');
    if (!house || !house.grid) {
        gridContainer.innerHTML = '<p style="padding: 20px; color: #999;">Aucun plan disponible. Cliquez sur "🏠 Éditer intérieur" pour créer le plan.</p>';
        return;
    }
    
    const grid = house.grid;
    const cellSize = 45; // Taille agrandie pour les icônes
    
    // Vérifier les filtres (vérifier si la checkbox est explicitement cochée)
    const showSensors = document.getElementById('show-sensors')?.checked === true;
    const showEquipments = document.getElementById('show-equipments')?.checked === true;
    
    // Créer le tableau HTML
    let html = '<table style="border-collapse: collapse;">';
    
    for (let i = 0; i < grid.length; i++) {
        html += '<tr>';
        for (let j = 0; j < grid[i].length; j++) {
            const cellData = grid[i][j];
            const baseValue = getCellBase(cellData);
            const cellSensors = getCellSensors(cellData);
            const cellEquipments = getCellEquipments(cellData);
            
            let bgColor = '#fff';
            let cellContent = '';
            let tooltipText = '';
            const overlays = [];
            
            // 1. Couche de base (pièce/mur/vide)
            if (baseValue === 1) {
                // Mur (extérieur)
                bgColor = '#e0e0e0';
                tooltipText = 'Extérieur';
            } else if (baseValue >= 2000 && baseValue < 3000) {
                // Pièce (codée comme 2000 + room.id)
                const roomId = baseValue - 2000;
                const room = rooms.find(r => r.id === roomId);
                if (room) {
                    tooltipText = room.name;
                    
                    // Afficher la couleur et le nom UNIQUEMENT si ni capteurs ni équipements ne sont affichés
                    if (!showSensors && !showEquipments) {
                        // Couleur aléatoire basée sur l'ID
                        const hue = (roomId * 137.5) % 360;
                        bgColor = `hsl(${hue}, 70%, 85%)`;
                        // Afficher le nom abrégé (3 premières lettres)
                        cellContent = `<div style="font-size: 10px; color: #555; font-weight: 600; text-align: center; line-height: 1.2;">${room.name.substring(0, 3)}</div>`;
                    }
                }
            } else {
                // Cellule vide
                tooltipText = 'Vide';
            }
            
            // 2. Overlay pour capteurs
            if (showSensors && cellSensors.length > 0) {
                const opacity = Math.min(0.15 + (cellSensors.length * 0.1), 0.5);
                overlays.push(`<div style="position: absolute; inset: 0; background: rgba(40, 167, 69, ${opacity}); border: 1px dashed #28a745; pointer-events: none; z-index: 1;"></div>`);
                
                const sensorNames = cellSensors.map(id => {
                    const sensor = sensors.find(s => s.id === id);
                    return sensor ? sensor.name : `Sensor ${id}`;
                });
                tooltipText += (tooltipText ? ' | ' : '') + '🌡️ ' + sensorNames.join(', ');
            }
            
            // 3. Overlay pour équipements
            if (showEquipments && cellEquipments.length > 0) {
                const opacity = Math.min(0.15 + (cellEquipments.length * 0.1), 0.5);
                overlays.push(`<div style="position: absolute; inset: 0; background: rgba(255, 193, 7, ${opacity}); border: 1px dashed #ffc107; pointer-events: none; z-index: 1;"></div>`);
                
                const equipNames = cellEquipments.map(id => {
                    const equip = equipments.find(e => e.id === id);
                    return equip ? equip.name : `Equipment ${id}`;
                });
                tooltipText += (tooltipText ? ' | ' : '') + '⚙️ ' + equipNames.join(', ');
            }
            
            // 4. Icônes
            const icons = [];
            
            if (showSensors && cellSensors.length > 0) {
                cellSensors.forEach(id => {
                    const sensor = sensors.find(s => s.id === id);
                    if (sensor) {
                        const icon = getSensorIcon(sensor.type);
                        const stateColor = sensor.is_active ? '#28a745' : '#999';
                        icons.push(`<span style="color: ${stateColor}; font-size: 14px;" title="${sensor.name}: ${sensor.value || 0}${sensor.unit || ''}">${icon}</span>`);
                    }
                });
            }
            
            // Variable pour stocker le style de bordure de la cellule (pour les portes)
            let cellBorderStyle = '';
            
            if (showEquipments && cellEquipments.length > 0) {
                cellEquipments.forEach(id => {
                    const equipment = equipments.find(e => e.id === id);
                    if (equipment) {
                        console.log(`[Grid] Equipment ${equipment.id} (${equipment.name}): type=${equipment.type}, state="${equipment.state}"`);
                        
                        let displayIcon = '';
                        let stateText = '';
                        
                        // Normaliser l'état (gérer 'on'/'off' et 'open'/'closed')
                        const isOpen = equipment.state === 'open' || equipment.state === 'on';
                        const isClosed = equipment.state === 'closed' || equipment.state === 'off';
                        
                        // Utiliser des emojis d'état pour chaque type d'équipement
                        if (equipment.type === 'shutter') {
                            displayIcon = isOpen ? '⬆️' : '⬇️';
                            stateText = isOpen ? 'Ouvert' : 'Fermé';
                            icons.push(`<span style="
                                display: inline-block;
                                font-size: 22px;
                                margin: 1px;
                            " title="${equipment.name}: ${stateText}">${displayIcon}</span>`);
                        } else if (equipment.type === 'door') {
                            // Pour les portes fermées, ajouter un contour rouge à la case
                            stateText = isOpen ? 'Ouverte' : 'Fermée';
                            if (isClosed) {
                                cellBorderStyle = 'border: 3px solid #dc3545 !important;';
                            }
                            // Pas d'icône pour les portes, juste le contour rouge si fermée
                        } else if (equipment.type === 'sound_system') {
                            displayIcon = equipment.state === 'on' ? '🔊' : '🔇';
                            stateText = equipment.state === 'on' ? 'Activé' : 'Désactivé';
                            icons.push(`<span style="
                                display: inline-block;
                                font-size: 22px;
                                margin: 1px;
                            " title="${equipment.name}: ${stateText}">${displayIcon}</span>`);
                        } else if (equipment.type === 'light') {
                            // Pour les lumières, modifier la surbrillance de la case (pas d'icône)
                            stateText = equipment.state === 'on' ? 'Allumée' : 'Éteinte';
                            if (equipment.state === 'on') {
                                // Ajouter une surbrillance jaune à la cellule
                                bgColor = '#fff9c4'; // Jaune lumineux
                            }
                        }
                    }
                });
            }
            
            // 5. User avatars (always show users in simulation mode)
            let avatarHTML = '';
            const usersHere = [];
            for (const [userId, pos] of userPositions.entries()) {
                if (pos.x === j && pos.y === i) {
                    usersHere.push(pos);
                }
            }
            
            if (usersHere.length > 0) {
                // Si un seul utilisateur avec photo de profil, afficher la photo
                if (usersHere.length === 1 && usersHere[0].profile_image) {
                    avatarHTML = `<div style="position: absolute; top: 2px; left: 2px; z-index: 10;" title="${usersHere[0].username}">
                        <img src="${usersHere[0].profile_image}" alt="${usersHere[0].username}" style="width: 32px; height: 32px; border-radius: 50%; border: 2px solid rgba(23, 162, 184, 0.9); box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    </div>`;
                } else {
                    // Sinon, afficher le badge avec les noms
                    const usernames = usersHere.map(u => u.username).join(', ');
                    avatarHTML = `<div style="position: absolute; top: 2px; left: 2px; background: rgba(23, 162, 184, 0.9); color: white; padding: 2px 6px; border-radius: 10px; font-size: 11px; font-weight: bold; z-index: 10;">
                        👤 ${usernames}
                    </div>`;
                }
            }
            
            // Composer le contenu final
            let finalContent = overlays.join('');
            finalContent += avatarHTML;
            
            // Toujours afficher le nom de la pièce si disponible
            if (cellContent) {
                finalContent += `<div style="position: relative; z-index: 2;">${cellContent}</div>`;
            }
            
            // Ajouter les icônes des capteurs/équipements par dessus
            if (icons.length > 0) {
                finalContent += `<div style="position: relative; z-index: 3; display: flex; flex-wrap: wrap; gap: 2px; justify-content: center; margin-top: 2px;">${icons.join('')}</div>`;
            }
            
            const clickHandler = movementMode ? `onclick="handleCellClick(${j}, ${i})"` : '';
            const cursor = movementMode ? 'pointer' : (baseValue >= 2000 ? 'pointer' : 'default');
            
            html += `<td ${clickHandler} style="
                width: ${cellSize}px;
                height: ${cellSize}px;
                background: ${bgColor};
                border: 1px solid #ddd;
                ${cellBorderStyle}
                text-align: center;
                vertical-align: middle;
                position: relative;
                cursor: ${cursor};
            " title="${tooltipText}">${finalContent}</td>`;
        }
        html += '</tr>';
    }
    
    html += '</table>';
    gridContainer.innerHTML = html;
}

// Obtenir l'icône pour un type de capteur
function getSensorIcon(type) {
    const icons = {
        'temperature': '🌡️',
        'luminosity': '💡',
        'rain': '🌧️',
        'presence': '👤'
    };
    return icons[type] || '📊';
}

// Obtenir l'icône pour un type d'équipement
function getEquipmentIcon(type) {
    const icons = {
        'shutter': '🪟',
        'door': '🚪',
        'light': '💡',
        'sound_system': '🔊'
    };
    return icons[type] || '⚙️';
}

// Charger les capteurs
async function loadSensors() {
    try {
        const response = await fetch('/api/sensors');
        if (response.ok) {
            const data = await response.json();
            // Filtrer par house_id et trier par ID pour maintenir un ordre stable
            sensors = data.sensors
                .filter(s => s.house_id === parseInt(houseId))
                .sort((a, b) => a.id - b.id);
            // Mettre à jour la référence globale pour weather.js
            window.sensors = sensors;
            displaySensors();
        }
    } catch (error) {
        console.error('Erreur de chargement des capteurs', error);
    }
}

// Afficher les capteurs
function displaySensors() {
    const grid = document.getElementById('sensors-grid');
    const isAdmin = userRole === 'proprietaire' || userRole === 'admin';
    
    if (sensors.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted); padding: 1rem;">Aucun capteur. Ajoutez-en un !</p>';
        return;
    }
    
    grid.innerHTML = sensors.map(sensor => {
        const typeLabel = {
            temperature: 'Température',
            luminosity: 'Luminosité',
            rain: 'Pluie',
            presence: 'Présence'
        };
        
        const menuHtml = isAdmin ? `
                <div class="sensor-menu-container">
                    <button class="sensor-menu-btn" onclick="toggleSensorMenu(event, ${sensor.id})" title="Options">
                        ⋮
                    </button>
                    <div class="sensor-menu" id="sensor-menu-${sensor.id}">
                        <button onclick="showEditSensorModal(${sensor.id})">Modifier</button>
                        <button onclick="updateSensorValue(${sensor.id})">Mettre à jour</button>
                        <button onclick="deleteSensor(${sensor.id})" style="color: #ef4444;">Supprimer</button>
                    </div>
                </div>` : '';
        
        const typeIcon = {
            temperature: '🌡️',
            luminosity: '✨',
            rain: '🌧️',
            presence: '📡'
        };
        
        const typeUnit = {
            temperature: '°C',
            luminosity: 'lux',
            rain: 'mm',
            presence: ''
        };
        
        // Formatage spécial pour les capteurs de présence
        let displayValue;
        if (sensor.type === 'presence') {
            displayValue = sensor.value == 1 || sensor.value === true ? 'Détectée' : 'Non détectée';
        } else {
            displayValue = `<span class="sensor-value">${sensor.value || 0}</span> <span style="font-size: 1rem; color: var(--text-muted);">${sensor.unit || typeUnit[sensor.type] || ''}</span>`;
        }
        
        return `
            <div class="card" id="sensor-${sensor.id}" style="position: relative;">
                <div style="display: flex; align-items: start; gap: 0.75rem; margin-bottom: 0.75rem;">
                    <span style="font-size: 1.5rem; line-height: 1;">${typeIcon[sensor.type] || '📊'}</span>
                    <div style="flex: 1;">
                        <h4 style="margin: 0 0 0.25rem 0;">${sensor.name}</h4>
                        <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">${typeLabel[sensor.type] || sensor.type}</span>
                    </div>
                </div>
                ${menuHtml}
                <p style="font-size: 1.5rem; font-weight: 600; margin: 0.5rem 0; color: var(--text-primary);">
                    ${displayValue}
                </p>
                <p style="margin: 0.5rem 0;">
                    <span class="status-badge ${sensor.is_active ? 'status-active' : 'status-inactive'}">
                        ${sensor.is_active ? 'Actif' : 'Inactif'}
                    </span>
                </p>
            </div>
        `;
    }).join('');
}

// Charger les équipements
async function loadEquipments() {
    try {
        const response = await fetch('/api/equipments');
        if (response.ok) {
            const data = await response.json();
            // Filtrer par house_id
            equipments = data.equipments.filter(e => e.house_id === parseInt(houseId));
            displayEquipments();
        }
    } catch (error) {
        console.error('Erreur de chargement des équipements', error);
    }
}

// Afficher les équipements
function displayEquipments() {
    const grid = document.getElementById('equipments-grid');
    const isAdmin = userRole === 'proprietaire' || userRole === 'admin';
    
    if (equipments.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted); padding: 1rem;">Aucun équipement. Ajoutez-en un !</p>';
        return;
    }
    
    // Filtrer les équipements selon les permissions de l'utilisateur
    const visibleEquipments = equipments.filter(equipment => {
        // Le propriétaire voit toujours tout
        if (userRole === 'proprietaire') {
            return true;
        }
        // Si pas de restriction de rôles, tout le monde peut voir
        if (!equipment.allowed_roles || equipment.allowed_roles.length === 0) {
            return true;
        }
        // Sinon, vérifier si l'utilisateur a le bon rôle
        return userRole && equipment.allowed_roles.includes(userRole);
    });

    grid.innerHTML = visibleEquipments.map(equipment => {
        const typeInfo = {
            shutter: { label: 'Volet roulant', states: { open: 'Ouvert', closed: 'Fermé' } },
            door: { label: 'Porte', states: { open: 'Ouverte', closed: 'Fermée' } },
            light: { label: 'Lumière', states: { on: 'Allumée', off: 'Éteinte' } },
            sound_system: { label: 'Système sonore', states: { on: 'Activé', off: 'Désactivé' } }
        };
        
        const info = typeInfo[equipment.type] || { label: 'Équipement', states: {} };
        const state = equipment.state || 'off';
        const stateDisplay = info.states[state] || state;
        
        // Déterminer la couleur de la carte selon l'état
        let stateColor = '';
        let stateBadge = '';
        if (equipment.type === 'light') {
            stateColor = state === 'on' ? 'var(--warning-color)' : 'var(--text-muted)';
            stateBadge = state === 'on' ? 
                '<span style="display: inline-block; padding: 0.25rem 0.75rem; background: #fef3c7; color: #92400e; border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">Allumée</span>' :
                '<span style="display: inline-block; padding: 0.25rem 0.75rem; background: #f3f4f6; color: #6b7280; border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">Éteinte</span>';
        } else if (equipment.type === 'shutter') {
            stateColor = state === 'open' ? 'var(--success-color)' : 'var(--danger-color)';
            stateBadge = state === 'open' ? 
                '<span style="display: inline-block; padding: 0.25rem 0.75rem; background: #d1fae5; color: #065f46; border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">Ouvert</span>' :
                '<span style="display: inline-block; padding: 0.25rem 0.75rem; background: #fee2e2; color: #991b1b; border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">Fermé</span>';
        } else if (equipment.type === 'door') {
            stateColor = state === 'open' ? 'var(--success-color)' : 'var(--danger-color)';
            stateBadge = state === 'open' ? 
                '<span style="display: inline-block; padding: 0.25rem 0.75rem; background: #d1fae5; color: #065f46; border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">Ouverte</span>' :
                '<span style="display: inline-block; padding: 0.25rem 0.75rem; background: #fee2e2; color: #991b1b; border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">Fermée</span>';
        } else if (equipment.type === 'sound_system') {
            stateColor = state === 'on' ? 'var(--primary-color)' : 'var(--text-muted)';
            stateBadge = state === 'on' ? 
                '<span style="display: inline-block; padding: 0.25rem 0.75rem; background: #dbeafe; color: #1e3a8a; border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">Activé</span>' :
                '<span style="display: inline-block; padding: 0.25rem 0.75rem; background: #f3f4f6; color: #6b7280; border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">Désactivé</span>';
        }
        
        const menuHtml = isAdmin ? `
                <div class="equipment-menu-container">
                    <button class="equipment-menu-btn" onclick="toggleEquipmentMenu(event, ${equipment.id})" title="Options">
                        ⋮
                    </button>
                    <div class="equipment-menu" id="equipment-menu-${equipment.id}">
                        <button onclick="showEditRolesModal(${equipment.id}); closeEquipmentMenus();">Permissions</button>
                        <button onclick="showEditEquipmentModal(${equipment.id}); closeEquipmentMenus();">Modifier</button>
                        <button onclick="deleteEquipment(${equipment.id}); closeEquipmentMenus();" style="color: var(--danger-color);">Supprimer</button>
                    </div>
                </div>` : '';
        
        const typeIcon = {
            shutter: '🪟',
            door: '🚪',
            light: '💡',
            sound_system: '🔊'
        };
        
        return `
            <div class="card equipment-card" style="border-left: 3px solid ${stateColor}; cursor: pointer; position: relative;" 
                 onclick="handleEquipmentCardClick(event, ${equipment.id}, '${equipment.state}')" 
                 data-equipment-id="${equipment.id}">
                ${menuHtml}
                <div style="display: flex; align-items: start; gap: 0.75rem; margin-bottom: 0.75rem;">
                    <span style="font-size: 1.5rem; line-height: 1;">${typeIcon[equipment.type] || '⚙️'}</span>
                    <div style="flex: 1;">
                        <h4 style="margin: 0 0 0.25rem 0;">${equipment.name}</h4>
                        <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">${info.label}</span>
                    </div>
                </div>
                <div style="margin: 0.5rem 0;">
                    ${stateBadge}
                </div>
                <p style="margin: 0.5rem 0;">
                    <span class="status-badge ${equipment.is_active ? 'status-active' : 'status-inactive'}">
                        ${equipment.is_active ? 'Actif' : 'Inactif'}
                    </span>
                </p>
            </div>
        `;
    }).join('');
}

// Gestion des tabs
function showTab(tabName, sourceElement) {
    // Masquer tous les tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Afficher le tab sélectionné
    const tabContent = document.getElementById(`tab-${tabName}`);
    if (tabContent) {
        tabContent.classList.add('active');
    }
    
    // Activer le bouton d'onglet correspondant
    const tabButton = sourceElement || document.querySelector(`.tab[onclick*="'${tabName}'"]`);
    if (tabButton) {
        tabButton.classList.add('active');
    }
}

// Modals
function showAddSensorModal() {
    document.getElementById('sensor-form').reset();
    toggleSensorValueInput();
    document.getElementById('sensor-modal').style.display = 'block';
}

function toggleSensorValueInput() {
    const type = document.getElementById('sensor-type').value;
    const numericDiv = document.getElementById('sensor-value-numeric');
    const booleanDiv = document.getElementById('sensor-value-boolean');
    const boolLabel = document.getElementById('sensor-bool-label');
    
    if (type === 'rain' || type === 'presence') {
        numericDiv.style.display = 'none';
        booleanDiv.style.display = 'block';
        boolLabel.textContent = type === 'presence' ? 'Présence détectée' : 'Pluie détectée';
    } else {
        numericDiv.style.display = 'block';
        booleanDiv.style.display = 'none';
    }
}

function showAddEquipmentModal() {
    document.getElementById('equipment-form').reset();
    document.getElementById('equipment-modal').style.display = 'block';
}

function closeModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

// CRUD Capteurs
document.getElementById('sensor-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const type = document.getElementById('sensor-type').value;
    let value;
    
    if (type === 'rain' || type === 'presence') {
        value = document.getElementById('sensor-value-bool').checked ? 1 : 0;
    } else {
        value = parseFloat(document.getElementById('sensor-value').value) || 0;
    }
    
    const data = {
        house_id: parseInt(houseId),
        name: document.getElementById('sensor-name').value,
        type: type,
        value: value
    };
    
    try {
        const response = await fetch('/api/sensors', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModals();
            await loadSensors();
        } else {
            alert('Erreur lors de la création');
        }
    } catch (error) {
        alert('Erreur de connexion');
    }
});

async function updateSensorValue(sensorId) {
    const sensor = sensors.find(s => s.id === sensorId);
    if (!sensor) return;
    
    let newValue;
    
    if (sensor.type === 'rain' || sensor.type === 'presence') {
        const label = sensor.type === 'presence' ? 'Présence détectée' : 'Pluie détectée';
        const confirmed = confirm(`${label} ?\n\nOK = Oui (1)\nAnnuler = Non (0)`);
        newValue = confirmed ? 1 : 0;
    } else {
        const input = prompt('Nouvelle valeur:');
        if (input === null) return;
        newValue = parseFloat(input);
    }
    
    try {
        const response = await fetch(`/api/sensors/${sensorId}/value`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value: newValue })
        });
        
        if (response.ok) {
            await loadSensors();
        }
    } catch (error) {
        alert('Erreur de mise à jour');
    }
}

async function deleteSensor(sensorId) {
    if (!confirm('Supprimer ce capteur ?')) return;
    
    try {
        const response = await fetch(`/api/sensors/${sensorId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await loadSensors();
        }
    } catch (error) {
        alert('Erreur de suppression');
    }
}

// CRUD Équipements
document.getElementById('equipment-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const type = document.getElementById('equipment-type').value;
    
    // Définir l'état par défaut selon le type
    let defaultState;
    if (type === 'shutter' || type === 'door') {
        defaultState = 'closed'; // Portes et volets fermés par défaut
    } else {
        defaultState = 'off'; // Lumières et systèmes sonores éteints par défaut
    }
    
    // Récupérer les rôles autorisés
    const roleCheckboxes = document.querySelectorAll('.equipment-role-checkbox:checked');
    const allowedRoles = Array.from(roleCheckboxes).map(cb => cb.value);
    
    const data = {
        house_id: houseId,
        name: document.getElementById('equipment-name').value,
        type: type,
        state: defaultState
    };
    
    // Ajouter allowed_roles seulement si au moins un rôle est sélectionné
    if (allowedRoles.length > 0) {
        data.allowed_roles = allowedRoles;
    }
    
    try {
        const response = await fetch('/api/equipments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModals();
            await loadEquipments();
        } else {
            alert('Erreur lors de la création');
        }
    } catch (error) {
        alert('Erreur de connexion');
    }
});

async function toggleEquipment(equipmentId, currentState) {
    // Trouver l'équipement pour connaître son type
    const equipment = equipments.find(e => e.id === equipmentId);
    if (!equipment) return;
    
    // Déterminer le nouvel état selon le type
    let newState;
    if (equipment.type === 'shutter' || equipment.type === 'door') {
        // Pour portes et volets : open/closed
        newState = (currentState === 'open') ? 'closed' : 'open';
    } else {
        // Pour lumières et systèmes sonores : on/off
        newState = (currentState === 'on') ? 'off' : 'on';
    }
    
    console.log(`[Toggle] Equipment ${equipmentId} (${equipment.type}): ${currentState} → ${newState}`);
    
    try {
        const response = await fetch(`/api/equipments/${equipmentId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ state: newState })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Mettre à jour uniquement l'équipement modifié dans le tableau local
            const index = equipments.findIndex(e => e.id === equipmentId);
            if (index !== -1) {
                equipments[index] = data;
            }
            
            // Rafraîchir l'affichage sans recharger depuis l'API
            displayEquipments();
            displayHouseGrid();
        }
    } catch (error) {
        alert('Erreur de mise à jour');
    }
}

async function deleteEquipment(equipmentId) {
    if (!confirm('Supprimer cet équipement ?')) return;
    
    try {
        const response = await fetch(`/api/equipments/${equipmentId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await loadEquipments();
        }
    } catch (error) {
        alert('Erreur de suppression');
    }
}

// Gérer les permissions d'un équipement
let currentEditEquipmentId = null;
let currentEditSensorId = null;

// Gestion du clic sur la carte d'équipement
function handleEquipmentCardClick(event, equipmentId, currentState) {
    // Ne pas activer le toggle si on clique sur le menu ou ses boutons
    if (event.target.closest('.equipment-menu-container')) {
        return;
    }
    toggleEquipment(equipmentId, currentState);
}

// Gestion du menu trois points
function toggleEquipmentMenu(event, equipmentId) {
    event.stopPropagation(); // Empêcher le toggle de l'équipement
    
    const menu = document.getElementById(`equipment-menu-${equipmentId}`);
    const allMenus = document.querySelectorAll('.equipment-menu');
    
    // Fermer tous les autres menus
    allMenus.forEach(m => {
        if (m !== menu) {
            m.classList.remove('show');
        }
    });
    
    // Toggle le menu actuel
    menu.classList.toggle('show');
}

// Fermer tous les menus
function closeEquipmentMenus() {
    document.querySelectorAll('.equipment-menu').forEach(menu => {
        menu.classList.remove('show');
    });
}

// Fermer les menus quand on clique ailleurs
document.addEventListener('click', (event) => {
    if (!event.target.closest('.equipment-menu-container')) {
        closeEquipmentMenus();
    }
    if (!event.target.closest('.sensor-menu-container')) {
        closeSensorMenus();
    }
    if (!event.target.closest('.rule-menu-container')) {
        closeRuleMenus();
    }
    if (!event.target.closest('.header-menu-btn') && !event.target.closest('.header-menu')) {
        closeHeaderMenu();
    }
    if (!event.target.closest('#plan-menu') && !event.target.closest('.header-menu-btn[onclick*="togglePlanMenu"]')) {
        closePlanMenu();
    }
});

// Rule menu functions
function toggleRuleMenu(event, ruleId) {
    event.stopPropagation();
    
    const menu = document.getElementById(`rule-menu-${ruleId}`);
    const allMenus = document.querySelectorAll('.rule-menu');
    
    // Fermer tous les autres menus
    allMenus.forEach(m => {
        if (m !== menu) {
            m.classList.remove('show');
        }
    });
    
    // Toggle le menu actuel
    menu.classList.toggle('show');
}

function closeRuleMenus() {
    document.querySelectorAll('.rule-menu').forEach(menu => {
        menu.classList.remove('show');
    });
}

// Header menu functions
function toggleHeaderMenu(event) {
    event.stopPropagation();
    
    const menu = document.getElementById('header-menu');
    menu.classList.toggle('show');
}

function closeHeaderMenu() {
    const menu = document.getElementById('header-menu');
    if (menu) {
        menu.classList.remove('show');
    }
}

// Plan menu functions
function togglePlanMenu(event) {
    event.stopPropagation();
    
    const menu = document.getElementById('plan-menu');
    menu.classList.toggle('show');
}

function closePlanMenu() {
    const menu = document.getElementById('plan-menu');
    if (menu) {
        menu.classList.remove('show');
    }
}

function showEditInteriorModal() {
    closePlanMenu();
    openGridEditor();
}

// Sensor menu functions
function toggleSensorMenu(event, sensorId) {
    event.stopPropagation();
    
    const menu = document.getElementById(`sensor-menu-${sensorId}`);
    const allMenus = document.querySelectorAll('.sensor-menu');
    
    // Fermer tous les autres menus
    allMenus.forEach(m => {
        if (m !== menu) {
            m.classList.remove('show');
        }
    });
    
    // Toggle le menu actuel
    menu.classList.toggle('show');
}

function closeSensorMenus() {
    document.querySelectorAll('.sensor-menu').forEach(menu => {
        menu.classList.remove('show');
    });
}

// Modal de modification de capteur
function showEditSensorModal(sensorId) {
    const sensor = sensors.find(s => s.id === sensorId);
    
    if (!sensor) {
        alert('Capteur introuvable');
        return;
    }
    
    currentEditSensorId = sensorId;
    
    document.getElementById('edit-sensor-name').value = sensor.name;
    document.getElementById('edit-sensor-modal').style.display = 'flex';
    
    closeSensorMenus();
}

async function submitEditSensor() {
    const sensorId = currentEditSensorId;
    const name = document.getElementById('edit-sensor-name').value.trim();
    
    if (!name) {
        alert('Le nom du capteur est requis');
        return;
    }
    
    try {
        const response = await fetch(`/api/sensors/${sensorId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        
        if (response.ok) {
            await loadSensors();
            document.getElementById('edit-sensor-modal').style.display = 'none';
        } else {
            const error = await response.json();
            alert(error.message || 'Erreur lors de la modification');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la modification');
    }
}

// Modal de modification d'équipement
function showEditEquipmentModal(equipmentId) {
    const equipment = equipments.find(e => e.id === equipmentId);
    
    if (!equipment) {
        alert('Équipement introuvable');
        return;
    }
    
    currentEditEquipmentId = equipmentId;
    
    // Vérifier les dépendances
    const dependencies = checkEquipmentDependencies(equipmentId);
    const warningDiv = document.getElementById('edit-equipment-warning');
    
    if (dependencies.hasRules) {
        const rulesList = dependencies.rules.map(r => 
            `<li style="margin: 0.25rem 0;">
                <strong>${r.name}</strong> 
                <span style="font-size: 0.8125rem; color: #92400e;">(${r.sensor?.name || 'Capteur'} → ${r.equipment?.name || 'Équipement'} → ${r.action_state})</span>
            </li>`
        ).join('');
        
        warningDiv.innerHTML = `
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 0.75rem; border-radius: 4px; margin-bottom: 1rem;">
                <strong>⚠️ Attention :</strong> Cet équipement est utilisé dans ${dependencies.rules.length} règle(s) d'automatisation :
                <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">${rulesList}</ul>
                <small style="color: #92400e; display: block; margin-top: 0.5rem;">
                    La modification du type peut créer des incohérences (états incompatibles : on/off vs open/closed).
                </small>
            </div>
            <div class="form-group" style="margin-bottom: 1rem;">
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                    <input type="checkbox" id="auto-resolve-conflicts" style="width: auto; cursor: pointer;">
                    <span>🔧 Résoudre automatiquement les conflits</span>
                </label>
                <small style="color: var(--text-muted); display: block; margin-top: 0.25rem; margin-left: 1.5rem;">
                    Les règles avec des états incompatibles seront supprimées automatiquement
                </small>
            </div>
        `;
        warningDiv.style.display = 'block';
    } else {
        warningDiv.style.display = 'none';
    }
    
    // Remplir le formulaire
    document.getElementById('edit-equipment-name').value = equipment.name;
    document.getElementById('edit-equipment-type').value = equipment.type;
    
    // Stocker le type original pour détecter les changements
    document.getElementById('edit-equipment-type').dataset.originalType = equipment.type;
    
    // Afficher le modal
    document.getElementById('edit-equipment-modal').style.display = 'block';
}

// Vérifier les dépendances d'un équipement
function checkEquipmentDependencies(equipmentId) {
    const dependencies = {
        hasRules: false,
        rules: []
    };
    
    // Vérifier les règles d'automatisation
    const relatedRules = automationRules.filter(rule => rule.equipment_id === equipmentId);
    if (relatedRules.length > 0) {
        dependencies.hasRules = true;
        dependencies.rules = relatedRules;
    }
    
    return dependencies;
}

// Vérifier si un état est compatible avec un type d'équipement
function isStateCompatible(equipmentType, state) {
    const shutterDoorStates = ['open', 'closed'];
    const lightSoundStates = ['on', 'off'];
    
    if (equipmentType === 'shutter' || equipmentType === 'door') {
        return shutterDoorStates.includes(state);
    } else if (equipmentType === 'light' || equipmentType === 'sound_system') {
        return lightSoundStates.includes(state);
    }
    return true;
}

// Trouver les règles avec états incompatibles
function findIncompatibleRules(equipmentId, newType) {
    return automationRules.filter(rule => {
        if (rule.equipment_id !== equipmentId) return false;
        return !isStateCompatible(newType, rule.action_state);
    });
}

// Supprimer plusieurs règles
async function deleteMultipleRules(ruleIds) {
    const results = { success: [], failed: [] };
    
    for (const ruleId of ruleIds) {
        try {
            const response = await fetch(`/api/automation/rules/${ruleId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                results.success.push(ruleId);
            } else {
                results.failed.push(ruleId);
            }
        } catch (error) {
            results.failed.push(ruleId);
        }
    }
    
    return results;
}

// Soumettre la modification d'équipement
async function submitEditEquipment(e) {
    e.preventDefault();
    
    if (!currentEditEquipmentId) return;
    
    const name = document.getElementById('edit-equipment-name').value.trim();
    const type = document.getElementById('edit-equipment-type').value;
    const originalType = document.getElementById('edit-equipment-type').dataset.originalType;
    const autoResolve = document.getElementById('auto-resolve-conflicts')?.checked || false;
    
    if (!name) {
        alert('Le nom est requis');
        return;
    }
    
    // Si le type change et qu'il y a des règles avec états incompatibles
    if (type !== originalType) {
        const incompatibleRules = findIncompatibleRules(currentEditEquipmentId, type);
        
        if (incompatibleRules.length > 0) {
            if (autoResolve) {
                // Résolution automatique : supprimer les règles incompatibles
                const confirmed = confirm(
                    `🔧 Résolution automatique activée\n\n` +
                    `${incompatibleRules.length} règle(s) avec des états incompatibles seront supprimées :\n` +
                    incompatibleRules.map(r => `• ${r.name} (action: ${r.action_state})`).join('\n') +
                    `\n\nVoulez-vous continuer ?`
                );
                
                if (!confirmed) return;
                
                // Supprimer les règles incompatibles
                const deleteResults = await deleteMultipleRules(incompatibleRules.map(r => r.id));
                
                if (deleteResults.failed.length > 0) {
                    alert(`⚠️ Erreur : ${deleteResults.failed.length} règle(s) n'ont pas pu être supprimées. Veuillez réessayer.`);
                    return;
                }
            } else {
                // Sans résolution auto : juste avertir
                const dependencies = checkEquipmentDependencies(currentEditEquipmentId);
                const ruleNames = dependencies.rules.map(r => r.name).join(', ');
                const confirmed = confirm(
                    `⚠️ ATTENTION : ${incompatibleRules.length} règle(s) auront des états incompatibles :\n` +
                    incompatibleRules.map(r => `• ${r.name} (état actuel: "${r.action_state}" incompatible avec le nouveau type)`).join('\n') +
                    `\n\nCes règles ne fonctionneront plus correctement.\n\n` +
                    `💡 Conseil : Cochez "Résoudre automatiquement" pour supprimer ces règles.\n\n` +
                    `Voulez-vous continuer quand même ?`
                );
                
                if (!confirmed) return;
            }
        }
    }
    
    const data = { name, type };
    
    try {
        const response = await fetch(`/api/equipments/${currentEditEquipmentId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModals();
            await loadEquipments();
            await loadAutomationRules(); // Recharger les règles
            displayHouseGrid(); // Rafraîchir la grille
            
            if (type !== originalType) {
                const incompatibleRules = findIncompatibleRules(currentEditEquipmentId, type);
                if (autoResolve && incompatibleRules.length > 0) {
                    alert(`Équipement modifié avec succès.\n\n${incompatibleRules.length} règle(s) incompatible(s) ont été supprimées automatiquement.`);
                } else {
                    alert('Équipement modifié avec succès.');
                }
            } else {
                alert('Équipement modifié avec succès');
            }
        } else {
            const error = await response.json();
            alert(error.error || 'Erreur lors de la modification');
        }
    } catch (error) {
        alert('Erreur de connexion');
    }
}

function showEditRolesModal(equipmentId) {
    currentEditEquipmentId = equipmentId;
    const equipment = equipments.find(e => e.id === equipmentId);
    
    if (!equipment) {
        alert('Équipement introuvable');
        return;
    }
    
    // Afficher le nom de l'équipement
    document.getElementById('edit-roles-equipment-name').textContent = 
        `Équipement : ${equipment.name}`;
    
    // Réinitialiser les checkboxes
    document.querySelectorAll('.edit-role-checkbox').forEach(cb => {
        cb.checked = false;
    });
    
    // Cocher les rôles autorisés actuels
    if (equipment.allowed_roles && equipment.allowed_roles.length > 0) {
        equipment.allowed_roles.forEach(role => {
            const checkbox = document.querySelector(`.edit-role-checkbox[value="${role}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }
    
    // Afficher le modal
    document.getElementById('edit-roles-modal').style.display = 'block';
}

// Gérer la soumission du formulaire de permissions
document.getElementById('edit-roles-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!currentEditEquipmentId) return;
    
    // Récupérer les rôles sélectionnés
    const roleCheckboxes = document.querySelectorAll('.edit-role-checkbox:checked');
    const allowedRoles = Array.from(roleCheckboxes).map(cb => cb.value);
    
    const data = {
        allowed_roles: allowedRoles.length > 0 ? allowedRoles : null
    };
    
    try {
        const response = await fetch(`/api/equipments/${currentEditEquipmentId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModals();
            await loadEquipments();
            alert('Permissions mises à jour avec succès');
        } else {
            alert('Erreur lors de la mise à jour des permissions');
        }
    } catch (error) {
        alert('Erreur de connexion');
    }
});

// Automatisation
async function triggerAutomation(silent = false) {
    try {
        const response = await fetch('/api/automation/trigger', {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Afficher le log uniquement si pas en mode silencieux
            if (!silent) {
                const log = document.getElementById('automation-log');
                if (log) {
                    log.innerHTML = `
                        <div class="card">
                            <h4>Automatisation exécutée</h4>
                            <p><strong>${data.actions_count}</strong> action(s) effectuée(s)</p>
                            ${data.actions.map(a => `
                                <p>→ ${a.action}: ${a.equipment_name}<br>
                                   <small>${a.reason}</small></p>
                            `).join('')}
                        </div>
                    `;
                }
            } else {
                // En mode silencieux, juste logger dans la console si des actions ont été effectuées
                if (data.actions_count > 0) {
                    console.log(`[Automatisation] ${data.actions_count} action(s) effectuée(s) automatiquement`);
                }
            }
            
            // Recharger les capteurs ET les équipements
            await Promise.all([
                loadSensors(),
                loadEquipments()
            ]);
        } else if (!silent) {
            const errorData = await response.json();
            alert('Erreur: ' + (errorData.error || 'Impossible de déclencher l\'automatisation'));
        }
    } catch (error) {
        console.error('Erreur d\'automatisation:', error);
        if (!silent) {
            alert('Erreur d\'automatisation');
        }
    }
}

// Navigation
function goBack() {
    window.location.href = '/app/dashboard.html';
}

function openGridEditor() {
    window.location.href = `/houses/edit_inside/${houseId}`;
}

// Variable pour stocker temporairement la grille
let tempGridData = null;

// Modifier la maison
function editHouse() {
    console.log('editHouse called with houseId:', houseId);
    if (!house) {
        alert('Données de la maison non chargées');
        return;
    }
    
    // Remplir le formulaire
    document.getElementById('edit-house-name').value = house.name;
    document.getElementById('edit-house-address').value = house.address || '';
    document.getElementById('edit-house-length').value = house.length;
    document.getElementById('edit-house-width').value = house.width;
    
    // Afficher le modal
    document.getElementById('edit-house-modal').style.display = 'block';
}

// Alias pour le menu
function showEditHouseModal() {
    closeHeaderMenu();
    editHouse();
}

// Fermer le modal de modification
function closeEditHouseModal() {
    document.getElementById('edit-house-modal').style.display = 'none';
}

// Soumettre la modification de maison
async function submitEditHouse(e) {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('edit-house-name').value,
        address: document.getElementById('edit-house-address').value
    };
    
    // Si on a une grille temporaire, l'ajouter aux données
    if (tempGridData) {
        data.grid = JSON.parse(tempGridData);
    }
    
    try {
        const response = await fetch(`/api/houses/${houseId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            house = await response.json();
            // Mettre à jour l'affichage
            document.getElementById('house-name').textContent = house.name;
            document.getElementById('house-title').textContent = house.name;
            document.getElementById('house-info').textContent = 
                `${house.address || 'Pas d\'adresse'} | ${house.length * house.width} m²`;
            
            // Rafraîchir le plan de la maison
            displayHouseGrid();
            
            // Nettoyer les données temporaires
            tempGridData = null;
            // Nettoyer l'URL
            window.history.replaceState({}, '', `/app/house.html?id=${houseId}`);
            
            closeEditHouseModal();
            alert('Maison modifiée avec succès');
        } else {
            const error = await response.json();
            alert('Erreur: ' + (error.error || 'Erreur inconnue'));
        }
    } catch (error) {
        console.error('Error updating house:', error);
        alert('Erreur de connexion au serveur');
    }
}

// Supprimer la maison
async function deleteHouse() {
    console.log('deleteHouse called with houseId:', houseId);
    if (!houseId) {
        alert('ID de maison manquant');
        return;
    }
    
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette maison ?')) return;
    
    try {
        const response = await fetch(`/api/houses/${houseId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Maison supprimée avec succès');
            window.location.href = '/app/dashboard.html';
        } else {
            const error = await response.json();
            alert('Erreur lors de la suppression: ' + (error.error || 'Erreur inconnue'));
        }
    } catch (error) {
        console.error('Error deleting house:', error);
        alert('Erreur de connexion au serveur');
    }
}

// ==================== AUTOMATION RULES ====================

// Charger les règles d'automatisation
async function loadAutomationRules() {
    try {
        const response = await fetch(`/api/automation/rules?house_id=${houseId}`);
        if (response.ok) {
            const data = await response.json();
            // Trier les règles par ID (ordre de création) pour maintenir un ordre stable
            automationRules = data.rules.sort((a, b) => a.id - b.id);
            displayAutomationRules();
            updateRuleSelects();
        }
    } catch (error) {
        console.error('Erreur de chargement des règles', error);
    }
}

// Afficher les règles d'automatisation
function displayAutomationRules() {
    const grid = document.getElementById('automation-rules-grid');
    const isAdmin = userRole === 'proprietaire' || userRole === 'admin';
    
    if (!grid) return;
    
    if (automationRules.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted); padding: 1rem;">Aucune règle. Créez votre première règle d\'automatisation !</p>';
        return;
    }
    
    grid.innerHTML = automationRules.map(rule => {
        const statusBadge = rule.is_active ? 
            '<span class="status-badge status-active">Activée</span>' :
            '<span class="status-badge status-inactive">Désactivée</span>';
        
        const operatorSymbol = {
            '>': '>',
            '<': '<',
            '>=': '≥',
            '<=': '≤',
            '==': '=',
            '!=': '≠'
        }[rule.condition_operator] || rule.condition_operator;
        
        const menuHtml = isAdmin ? `
                <div class="rule-menu-container">
                    <button class="rule-menu-btn" onclick="toggleRuleMenu(event, ${rule.id})" title="Options">
                        ⋮
                    </button>
                    <div class="rule-menu" id="rule-menu-${rule.id}">
                        <button onclick="toggleRule(${rule.id}, ${rule.is_active})">${rule.is_active ? 'Désactiver' : 'Activer'}</button>
                        <button onclick="editRule(${rule.id})">Modifier</button>
                        <button onclick="deleteRule(${rule.id})" style="color: #ef4444;">Supprimer</button>
                    </div>
                </div>` : '';
        
        return `
            <div class="card" style="position: relative;">
                ${menuHtml}
                <div style="display: flex; align-items: start; gap: 0.75rem; margin-bottom: 0.75rem;">
                    <span style="font-size: 1.5rem; line-height: 1;">⚙️</span>
                    <div style="flex: 1;">
                        <h4 style="margin: 0 0 0.25rem 0;">${rule.name}</h4>
                        ${rule.description ? `<p style="color: var(--text-muted); font-size: 0.8125rem; margin: 0;">${rule.description}</p>` : ''}
                    </div>
                </div>
                <div style="margin: 0.75rem 0; padding: 0.75rem; background: var(--background-color); border-left: 3px solid var(--primary-color); border-radius: 4px;">
                    <p style="margin: 0.25rem 0; font-size: 0.8125rem;"><strong>SI</strong> ${rule.sensor ? rule.sensor.name : 'Capteur'} ${operatorSymbol} ${rule.condition_value}</p>
                    <p style="margin: 0.25rem 0; font-size: 0.8125rem;"><strong>ALORS</strong> ${rule.equipment ? rule.equipment.name : 'Équipement'} → ${rule.action_state}</p>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 0.5rem 0;">
                    ${statusBadge}
                    <span style="font-size: 0.6875rem; color: var(--text-muted);">
                        ${new Date(rule.created_at).toLocaleDateString()}
                        ${rule.last_triggered ? ` • ${new Date(rule.last_triggered).toLocaleTimeString()}` : ''}
                    </span>
                </div>
            </div>
        `;
    }).join('');
}

// Variable pour suivre si on est en mode édition
let editingRuleId = null;

// Afficher le modal de création de règle
function showAddRuleModal() {
    editingRuleId = null; // Mode création
    document.getElementById('rule-form').reset();
    
    // Réinitialiser le conteneur d'actions
    const container = document.getElementById('rule-actions-container');
    container.innerHTML = '';
    ruleActionCounter = 0;
    
    // Réinitialiser le titre et bouton
    document.querySelector('#rule-modal h3').textContent = 'Créer une règle d\'automatisation';
    const submitBtn = document.querySelector('#rule-form button[type="submit"]');
    submitBtn.textContent = 'Créer la règle';
    
    // Afficher le modal puis mettre à jour les selects
    document.getElementById('rule-modal').style.display = 'block';
    updateRuleSelects();
}

// Mettre à jour les selects de capteurs et équipements pour les règles
function updateRuleSelects() {
    const sensorSelect = document.getElementById('rule-sensor');
    
    if (!sensorSelect) return;
    
    // Remplir les capteurs
    sensorSelect.innerHTML = sensors.map(s => 
        `<option value="${s.id}">${s.name} (${s.type})</option>`
    ).join('');
    
    // Ajouter la première action au chargement
    const container = document.getElementById('rule-actions-container');
    if (container && container.children.length === 0) {
        addRuleAction();
    }
}

// Compteur pour les IDs uniques des actions
let ruleActionCounter = 0;

// Ajouter une ligne équipement + action
function addRuleAction() {
    ruleActionCounter++;
    const container = document.getElementById('rule-actions-container');
    
    const actionDiv = document.createElement('div');
    actionDiv.className = 'rule-action-row';
    actionDiv.id = `rule-action-${ruleActionCounter}`;
    actionDiv.style.cssText = 'display: flex; gap: 10px; margin-bottom: 10px; align-items: center;';
    
    // Select équipement
    const equipmentSelect = document.createElement('select');
    equipmentSelect.className = 'rule-equipment-select';
    equipmentSelect.style.cssText = 'flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;';
    equipmentSelect.required = true;
    equipmentSelect.innerHTML = equipments.map(e => 
        `<option value="${e.id}">${e.name} (${e.type})</option>`
    ).join('');
    
    // Select action
    const actionSelect = document.createElement('select');
    actionSelect.className = 'rule-action-select';
    actionSelect.style.cssText = 'flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;';
    actionSelect.required = true;
    actionSelect.innerHTML = `
        <option value="on">Allumer / Activer</option>
        <option value="off">Éteindre / Désactiver</option>
        <option value="open">Ouvrir</option>
        <option value="closed">Fermer</option>
    `;
    
    // Bouton supprimer
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn btn-danger';
    removeBtn.textContent = '✖';
    removeBtn.style.cssText = 'padding: 8px 12px;';
    removeBtn.onclick = () => removeRuleAction(ruleActionCounter);
    
    actionDiv.appendChild(equipmentSelect);
    actionDiv.appendChild(actionSelect);
    actionDiv.appendChild(removeBtn);
    container.appendChild(actionDiv);
}

// Supprimer une ligne équipement + action
function removeRuleAction(actionId) {
    const actionDiv = document.getElementById(`rule-action-${actionId}`);
    if (actionDiv) {
        actionDiv.remove();
        // S'assurer qu'il reste au moins une action
        const container = document.getElementById('rule-actions-container');
        if (container.children.length === 0) {
            addRuleAction();
        }
    }
}

// Créer une nouvelle règle
document.getElementById('rule-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Si on est en mode édition, utiliser la fonction updateRule
    if (editingRuleId !== null) {
        await updateRule(editingRuleId);
        return;
    }
    
    // Mode création : code existant
    // Récupérer toutes les actions (équipements)
    const actionRows = document.querySelectorAll('.rule-action-row');
    const actions = [];
    
    actionRows.forEach(row => {
        const equipmentSelect = row.querySelector('.rule-equipment-select');
        const actionSelect = row.querySelector('.rule-action-select');
        
        if (equipmentSelect && actionSelect && equipmentSelect.value && actionSelect.value) {
            actions.push({
                equipment_id: parseInt(equipmentSelect.value),
                action_state: actionSelect.value
            });
        }
    });
    
    if (actions.length === 0) {
        alert('Veuillez ajouter au moins un équipement');
        return;
    }
    
    const baseData = {
        house_id: houseId,
        name: document.getElementById('rule-name').value,
        description: document.getElementById('rule-description').value || null,
        sensor_id: parseInt(document.getElementById('rule-sensor').value),
        condition_operator: document.getElementById('rule-operator').value,
        condition_value: parseFloat(document.getElementById('rule-value').value)
    };
    
    try {
        // Créer une règle pour chaque équipement
        let successCount = 0;
        let errorCount = 0;
        
        for (let i = 0; i < actions.length; i++) {
            const data = {
                ...baseData,
                name: actions.length > 1 ? `${baseData.name} (${i + 1})` : baseData.name,
                equipment_id: actions[i].equipment_id,
                action_state: actions[i].action_state
            };
            
            const response = await fetch('/api/automation/rules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                successCount++;
            } else {
                errorCount++;
            }
        }
        
        closeModals();
        await loadAutomationRules();
        
        if (errorCount === 0) {
            alert(`${successCount} règle(s) créée(s) avec succès !`);
        } else {
            alert(`${successCount} règle(s) créée(s), ${errorCount} erreur(s)`);
        }
    } catch (error) {
        alert('Erreur de connexion');
    }
});

// Activer/Désactiver une règle
async function toggleRule(ruleId, currentState) {
    try {
        const response = await fetch(`/api/automation/rules/${ruleId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: !currentState })
        });
        
        if (response.ok) {
            await loadAutomationRules();
        }
    } catch (error) {
        alert('Erreur lors de la modification');
    }
}

// Supprimer une règle
async function editRule(ruleId) {
    // Récupérer les détails de la règle
    try {
        const response = await fetch(`/api/automation/rules/${ruleId}`);
        if (!response.ok) {
            alert('Erreur lors du chargement de la règle');
            return;
        }
        
        const rule = await response.json();
        
        // Marquer qu'on est en mode édition
        editingRuleId = ruleId;
        
        // Pré-remplir le formulaire
        document.getElementById('rule-name').value = rule.name;
        document.getElementById('rule-description').value = rule.description || '';
        document.getElementById('rule-sensor').value = rule.sensor.id;
        document.getElementById('rule-operator').value = rule.condition_operator;
        document.getElementById('rule-value').value = rule.condition_value;
        
        // Réinitialiser le conteneur d'actions et ajouter l'action existante
        const container = document.getElementById('rule-actions-container');
        container.innerHTML = '';
        ruleActionCounter = 0;
        
        // Ajouter l'action existante
        addRuleAction();
        const equipmentSelect = container.querySelector('.rule-equipment-select');
        const actionSelect = container.querySelector('.rule-action-select');
        if (equipmentSelect && actionSelect) {
            equipmentSelect.value = rule.equipment.id;
            actionSelect.value = rule.action_state;
        }
        
        // Changer le titre et le bouton du modal
        document.querySelector('#rule-modal h3').textContent = 'Modifier la règle';
        const submitBtn = document.querySelector('#rule-form button[type="submit"]');
        submitBtn.textContent = 'Mettre à jour';
        
        // Afficher le modal
        document.getElementById('rule-modal').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading rule:', error);
        alert('Erreur lors du chargement de la règle');
    }
}

async function updateRule(ruleId) {
    const actionRows = document.querySelectorAll('.rule-action-row');
    if (actionRows.length === 0) {
        alert('Veuillez ajouter au moins un équipement');
        return;
    }
    
    const formData = {
        name: document.getElementById('rule-name').value,
        description: document.getElementById('rule-description').value || null,
        sensor_id: parseInt(document.getElementById('rule-sensor').value),
        condition_operator: document.getElementById('rule-operator').value,
        condition_value: parseFloat(document.getElementById('rule-value').value),
        equipment_id: parseInt(document.querySelector('.rule-equipment-select').value),
        action_state: document.querySelector('.rule-action-select').value
    };
    
    try {
        const response = await fetch(`/api/automation/rules/${ruleId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            editingRuleId = null; // Réinitialiser le mode
            closeModals();
            await loadAutomationRules();
            alert('Règle modifiée avec succès');
        } else {
            const error = await response.json();
            alert('Erreur: ' + (error.error || 'Impossible de modifier la règle'));
        }
    } catch (error) {
        console.error('Error updating rule:', error);
        alert('Erreur lors de la modification de la règle');
    }
}

async function deleteRule(ruleId) {
    if (!confirm('Supprimer cette règle d\'automatisation ?')) return;
    
    try {
        const response = await fetch(`/api/automation/rules/${ruleId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await loadAutomationRules();
            alert('Règle supprimée');
        }
    } catch (error) {
        alert('Erreur de suppression');
    }
}

// ==================== WEBSOCKET REAL-TIME UPDATES ====================

/**
 * Rafraîchit l'affichage d'un capteur dans la grille après une mise à jour WebSocket
 */
async function refreshSensorInGrid(sensorData) {
    console.log('🔄 [House] Rafraîchissement capteur temps réel:', sensorData);
    
    // Recharger les capteurs depuis l'API pour avoir les données complètes
    await loadSensors();
    
    // Rafraîchir la grille et la liste des capteurs
    displayHouseGrid();
    displaySensors();
    
    // Déclencher l'automatisation pour TOUS les capteurs
    // Cela permet aux règles d'automatisation de réagir en temps réel
    console.log('[House] Capteur changé, déclenchement automatisation automatique...');
    await triggerAutomation(true);
    console.log('[House] Automatisation déclenchée');
}

/**
 * Rafraîchit l'affichage d'un équipement dans la grille après une mise à jour WebSocket
 */
function refreshEquipmentInGrid(equipmentData) {
    console.log('[House] Rafraîchissement équipement WebSocket:', equipmentData);
    
    // Trouver et mettre à jour l'équipement dans le tableau local
    const index = equipments.findIndex(e => e.id === equipmentData.id);
    if (index !== -1) {
        // Mettre à jour les propriétés (garder les autres propriétés existantes)
        equipments[index].state = equipmentData.state;
        equipments[index].is_active = equipmentData.is_active;
        equipments[index].type = equipmentData.type || equipments[index].type;
        equipments[index].last_update = new Date().toISOString();
        
        console.log('[House] Équipement mis à jour:', {
            id: equipments[index].id,
            name: equipments[index].name,
            type: equipments[index].type,
            state: equipments[index].state,
            is_active: equipments[index].is_active
        });
        
        // Forcer le rafraîchissement de l'affichage
        console.log('[House] Rafraîchissement de l\'affichage...');
        displayEquipments();
        displayHouseGrid();
        console.log('[House] Affichage rafraîchi !');
    } else {
        console.warn('[House] Équipement non trouvé dans le tableau local, ID:', equipmentData.id);
        console.log('[House] Équipements disponibles:', equipments.map(e => ({id: e.id, name: e.name})));
    }
}

// ==================== MOVEMENT SIMULATION ====================

async function toggleMovementMode() {
    movementMode = !movementMode;
    
    // Update button visibility
    const simulateBtn = document.getElementById('simulate-btn');
    const stopBtn = document.getElementById('stop-simulate-btn');
    
    if (movementMode) {
        // Show stop button, hide simulate button
        if (simulateBtn) simulateBtn.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'block';
        
        // Initialize user at house entrance (outside)
        const entranceX = 0;
        const entranceY = 0;
        await updateMyPosition(entranceX, entranceY);
        
        // Refresh grid to show positions
        displayHouseGrid();
        
        console.log('Mode simulation activé');
    } else {
        // Show simulate button, hide stop button
        if (simulateBtn) simulateBtn.style.display = 'block';
        if (stopBtn) stopBtn.style.display = 'none';
        
        // Deactivate position
        await deactivateMyPosition();
        
        // Clear positions
        userPositions.clear();
        myPosition = null;
        
        // Refresh grid
        displayHouseGrid();
        
        console.log('Mode simulation désactivé');
    }
}

async function stopSimulation() {
    if (movementMode) {
        await toggleMovementMode();
    }
}

async function loadUserPositions() {
    try {
        const response = await fetch(`/api/houses/${houseId}/positions`);
        if (response.ok) {
            const data = await response.json();
            userPositions.clear();
            data.positions.forEach(pos => {
                userPositions.set(pos.user_id, {
                    x: pos.x,
                    y: pos.y,
                    username: pos.username,
                    profile_image: pos.profile_image
                });
            });
        }
    } catch (error) {
        console.error('Erreur chargement positions:', error);
    }
}

async function updateMyPosition(x, y) {
    try {
        const response = await fetch(`/api/houses/${houseId}/positions`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({x, y})
        });
        
        if (response.ok) {
            const data = await response.json();
            myPosition = {x, y};
            
            // Update local positions map
            userPositions.set(data.position.user_id, {
                x: data.position.x,
                y: data.position.y,
                username: data.position.username,
                profile_image: data.position.profile_image
            });
            
            // Check for presence sensors at new position
            activatePresenceSensors(x, y);
            
            return true;
        }
        return false;
    } catch (error) {
        console.error('Erreur mise à jour position:', error);
        return false;
    }
}

async function deactivateMyPosition() {
    try {
        await fetch(`/api/houses/${houseId}/positions`, {
            method: 'DELETE'
        });
    } catch (error) {
        console.error('Erreur désactivation position:', error);
    }
}

async function activatePresenceSensors(x, y) {
    // Find presence sensors at this position
    const cell = house.grid[y][x];
    const cellSensors = getCellSensors(cell);
    
    for (const sensorId of cellSensors) {
        const sensor = sensors.find(s => s.id === sensorId);
        if (sensor && sensor.type === 'presence') {
            // Activate sensor (set value to 1) programmatically
            try {
                const response = await fetch(`/api/sensors/${sensorId}/value`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ value: 1 })
                });
                
                if (response.ok) {
                    console.log(`Capteur de présence ${sensorId} activé`);
                }
            } catch (error) {
                console.error('Erreur activation capteur:', error);
            }
        }
    }
}

async function handleCellClick(x, y) {
    if (!movementMode) return;
    
    // Validate movement
    const canMove = canMoveTo(x, y);
    console.log(`[Movement] Click on (${x}, ${y}), canMove: ${canMove}`);
    
    if (!canMove) {
        const targetCell = house.grid[y][x];
        const targetBase = getCellBase(targetCell);
        console.log(`[Movement] Blocked! targetBase: ${targetBase}, myPosition:`, myPosition);
        alert('Déplacement impossible : mur ou porte fermée');
        return;
    }
    
    // Teleport to cell
    const success = await updateMyPosition(x, y);
    if (success) {
        displayHouseGrid();
    }
}

function canMoveTo(x, y) {
    console.log(`[Movement] canMoveTo(${x}, ${y}) called, myPosition:`, myPosition, `equipments count: ${equipments.length}`);
    
    // Use actual grid dimensions (not house.width/length which don't include exterior)
    const gridWidth = house.grid[0].length;
    const gridHeight = house.grid.length;
    console.log(`[Movement] Grid dimensions: width=${gridWidth}, height=${gridHeight}`);
    
    // Check bounds
    if (x < 0 || x >= gridWidth || y < 0 || y >= gridHeight) {
        console.log(`[Movement] Out of bounds - x=${x} >= ${gridWidth} OR y=${y} >= ${gridHeight}`);
        return false;
    }
    
    const targetCell = house.grid[y][x];
    const targetBase = getCellBase(targetCell);
    
    // Note: base === 1 represents exterior (not walls), users CAN move there
    // Only block if explicitly defined as impassable (reserved for future wall types)
    
    // If no current position (first move), allow movement
    if (!myPosition) {
        console.log('[Movement] First move, allowing');
        return true;
    }
    
    // Get current and target cells
    const currentCell = house.grid[myPosition.y][myPosition.x];
    const currentEquipments = getCellEquipments(currentCell);
    const targetEquipments = getCellEquipments(targetCell);
    
    // Find closed doors in current and target cells
    const currentClosedDoors = new Set();
    const targetClosedDoors = new Set();
    
    currentEquipments.forEach(eqId => {
        const eq = equipments.find(e => e.id === eqId);
        if (eq && eq.type === 'door' && eq.state === 'closed') {
            currentClosedDoors.add(eqId);
        }
    });
    
    targetEquipments.forEach(eqId => {
        const eq = equipments.find(e => e.id === eqId);
        if (eq && eq.type === 'door' && eq.state === 'closed') {
            targetClosedDoors.add(eqId);
        }
    });
    
    // Movement is allowed only if BOTH cells have EXACTLY the same set of closed doors
    // This ensures you can't cross a door from one side to the other
    
    // Convert Sets to arrays for comparison
    const currentDoorIds = Array.from(currentClosedDoors).sort();
    const targetDoorIds = Array.from(targetClosedDoors).sort();
    
    // Check if arrays are identical
    const sameClosedDoors = currentDoorIds.length === targetDoorIds.length &&
                            currentDoorIds.every((doorId, index) => doorId === targetDoorIds[index]);
    
    if (!sameClosedDoors) {
        console.log(`[Movement] Closed doors mismatch - current: [${currentDoorIds}], target: [${targetDoorIds}] - blocked`);
        return false;
    }
    
    if (currentClosedDoors.size > 0) {
        console.log(`[Movement] Both cells share the same closed doors [${currentDoorIds}] - allowing movement`);
    }
    
    console.log('[Movement] No closed doors blocking movement');
    return true;
}

// Handle WebSocket position updates
function handlePositionUpdate(data) {
    // Only process position updates for the current house
    if (data.house_id !== parseInt(houseId)) {
        console.log(`[Movement] Ignoring position update for house ${data.house_id} (current: ${houseId})`);
        return;
    }
    
    if (data.type === 'user_position_changed') {
        userPositions.set(data.user_id, {
            x: data.x,
            y: data.y,
            username: data.username,
            profile_image: data.profile_image
        });
        displayHouseGrid();
    } else if (data.type === 'user_position_deactivated') {
        userPositions.delete(data.user_id);
        displayHouseGrid();
    }
}

// ==================== INITIALIZATION ====================

// Attendre que le DOM soit chargé avant d'initialiser
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Cleanup: deactivate position when user leaves the page
window.addEventListener('beforeunload', () => {
    if (movementMode && myPosition) {
        // Use fetch with keepalive for reliable cleanup during page unload
        fetch(`/api/houses/${houseId}/positions`, {
            method: 'DELETE',
            keepalive: true
        }).catch(() => {
            // Ignore errors during unload
        });
    }
});
