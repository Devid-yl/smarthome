/**
 * Module de gestion de la météo
 */

let weatherData = null;
let weatherUpdateInterval = null;
let isManualMode = false;
let manualWeatherData = null;

/**
 * Charger les données météo depuis le cache localStorage
 */
function loadWeatherFromCache(houseId) {
    try {
        const cacheKey = `weather_${houseId}`;
        const cached = localStorage.getItem(cacheKey);
        if (cached) {
            const data = JSON.parse(cached);
            // Vérifier que le cache n'est pas trop vieux (max 1 heure)
            const now = Date.now();
            if (data.timestamp && (now - data.timestamp < 60 * 60 * 1000)) {
                weatherData = data;
                displayWeather();
                console.log('🌤️ [Weather] Données chargées depuis le cache');
                return true;
            }
        }
    } catch (error) {
        console.error('Erreur chargement cache météo:', error);
    }
    return false;
}

/**
 * Sauvegarder les données météo dans le cache localStorage
 */
function saveWeatherToCache(houseId, data) {
    try {
        const cacheKey = `weather_${houseId}`;
        const cacheData = {
            ...data,
            timestamp: Date.now()
        };
        localStorage.setItem(cacheKey, JSON.stringify(cacheData));
        console.log('💾 [Weather] Données sauvegardées en cache');
    } catch (error) {
        console.error('Erreur sauvegarde cache météo:', error);
    }
}

/**
 * Initialiser la météo pour une maison (démarrer l'interval de rafraîchissement)
 */
async function initWeather(houseId) {
    // Actualiser toutes les 10 minutes
    if (weatherUpdateInterval) {
        clearInterval(weatherUpdateInterval);
    }
    weatherUpdateInterval = setInterval(() => {
        loadWeather(houseId);
    }, 10 * 60 * 1000); // 10 minutes
}

/**
 * Charger les données météo
 */
async function loadWeather(houseId) {
    try {
        const response = await fetch(`/api/weather/${houseId}`);
        if (response.ok) {
            weatherData = await response.json();
            // Sauvegarder dans le cache
            saveWeatherToCache(houseId, weatherData);
            displayWeather();
            // Synchroniser automatiquement avec les capteurs
            syncWeatherToSensorsAuto();
            return weatherData;
        } else {
            console.warn('Could not load weather data');
            hideWeatherWidget();
        }
    } catch (error) {
        console.error('Error loading weather:', error);
        hideWeatherWidget();
    }
}

/**
 * Afficher le widget météo
 */
function displayWeather() {
    if (!weatherData) return;
    
    const container = document.getElementById('weather-widget');
    if (!container) return;
    
    // Utiliser les données manuelles si le mode manuel est activé
    const currentData = isManualMode && manualWeatherData ? manualWeatherData : weatherData;
    
    const modeIndicator = isManualMode ? 
        '<div class="weather-manual-indicator">Mode Manuel</div>' : '';
    
    container.style.display = 'block';
    container.innerHTML = `
        <div class="weather-card ${isManualMode ? 'weather-manual-mode' : ''}">
            ${modeIndicator}
            <div class="weather-header">
                <span class="weather-emoji">${currentData.emoji || '🌍'}</span>
                <div class="weather-location">
                    <strong>${currentData.location?.city || weatherData.location?.city || 'Inconnu'}</strong>
                    <small>${currentData.weather_description}</small>
                </div>
            </div>
            <div class="weather-details">
                <div class="weather-item">
                    <span class="weather-icon">🌡️</span>
                    <span class="weather-label">Température</span>
                    <span class="weather-value">${currentData.temperature}°C</span>
                </div>
                <div class="weather-item">
                    <span class="weather-icon">💡</span>
                    <span class="weather-label">Luminosité</span>
                    <span class="weather-value">${Math.round(currentData.luminosity)} lux</span>
                </div>
                <div class="weather-item">
                    <span class="weather-icon">🌧️</span>
                    <span class="weather-label">Pluie</span>
                    <span class="weather-value">${currentData.rain} mm</span>
                </div>
                <div class="weather-item">
                    <span class="weather-icon">💨</span>
                    <span class="weather-label">Vent</span>
                    <span class="weather-value">${currentData.wind_speed} km/h</span>
                </div>
            </div>
            <div class="weather-controls">
                ${isManualMode ? `
                    <button class="btn btn-primary" onclick="showManualWeatherForm()">
                        Modifier valeurs
                    </button>
                    <button class="btn btn-secondary" onclick="switchToRealWeather()">
                        Repasser au réel
                    </button>
                ` : `
                    <button class="btn btn-primary" onclick="switchToManualMode()">
                        Mode manuel
                    </button>
                `}
            </div>
        </div>
    `;
}

/**
 * Masquer le widget météo
 */
function hideWeatherWidget() {
    const container = document.getElementById('weather-widget');
    if (container) {
        container.style.display = 'none';
    }
}

/**
 * Passer en mode manuel
 */
function switchToManualMode() {
    isManualMode = true;
    // Copier les données réelles comme base pour le mode manuel
    manualWeatherData = JSON.parse(JSON.stringify(weatherData));
    displayWeather();
    syncWeatherToSensorsAuto();
}

/**
 * Repasser en mode réel
 */
function switchToRealWeather() {
    isManualMode = false;
    manualWeatherData = null;
    displayWeather();
    syncWeatherToSensorsAuto();
}

/**
 * Afficher le formulaire de modification manuelle
 */
function showManualWeatherForm() {
    const current = manualWeatherData || weatherData;
    const form = prompt(
        `Modifier la météo manuellement:\n\n` +
        `Entrez les valeurs séparées par des virgules:\n` +
        `Température (°C), Luminosité (lux), Pluie (mm), Vent (km/h)\n\n` +
        `Exemple: 30, 5000, 0, 15`,
        `${current.temperature}, ${Math.round(current.luminosity)}, ${current.rain}, ${current.wind_speed}`
    );
    
    if (form) {
        const values = form.split(',').map(v => parseFloat(v.trim()));
        if (values.length === 4 && values.every(v => !isNaN(v))) {
            manualWeatherData = {
                ...current,
                temperature: values[0],
                luminosity: values[1],
                rain: values[2],
                wind_speed: values[3],
                weather_description: getWeatherDescription(values[0], values[1], values[2]),
                emoji: getWeatherEmoji(values[0], values[1], values[2])
            };
            displayWeather();
            syncWeatherToSensorsAuto();
        } else {
            alert('Format invalide. Veuillez entrer 4 valeurs numériques.');
        }
    }
}

/**
 * Obtenir une description météo basée sur les valeurs
 */
function getWeatherDescription(temp, lux, rain) {
    if (rain > 1) return 'Pluvieux';
    if (lux < 1000) return 'Nuit';
    if (lux < 10000) return 'Nuageux';
    if (temp > 30) return 'Très chaud';
    if (temp > 25) return 'Ensoleillé';
    if (temp < 10) return 'Froid';
    return 'Dégagé';
}

/**
 * Obtenir un emoji météo basé sur les valeurs
 */
function getWeatherEmoji(temp, lux, rain) {
    if (rain > 1) return '🌧️';
    if (lux < 1000) return '🌙';
    if (lux < 10000) return '☁️';
    if (temp > 30) return '🔥';
    return '☀️';
}

/**
 * Synchroniser automatiquement les capteurs avec la météo actuelle
 */
async function syncWeatherToSensorsAuto() {
    const currentData = isManualMode && manualWeatherData ? manualWeatherData : weatherData;
    
    console.log('🌤️ [Weather] Synchronisation météo vers capteurs...', currentData);
    
    if (!currentData || !window.sensors) {
        console.warn('⚠️ [Weather] Données météo ou capteurs manquants');
        return;
    }
    
    // Trouver les capteurs météo et les mettre à jour
    for (const sensor of window.sensors) {
        let newValue = null;
        
        if (sensor.type === 'temperature') {
            newValue = currentData.temperature;
        } else if (sensor.type === 'luminosity') {
            newValue = currentData.luminosity;
        } else if (sensor.type === 'rain') {
            // Convertir les mm en booléen (1 = il pleut si > 0.1mm, 0 = pas de pluie)
            newValue = currentData.rain > 0.1 ? 1 : 0;
        }
        
        if (newValue !== null) {
            try {
                console.log(`🔄 [Weather] Mise à jour capteur ${sensor.type} #${sensor.id}: ${newValue}`);
                const response = await fetch(`/api/sensors/${sensor.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ value: newValue })
                });
                if (response.ok) {
                    console.log(`[Weather] Capteur ${sensor.type} #${sensor.id} mis à jour`);
                }
            } catch (error) {
                console.error(`[Weather] Erreur mise à jour capteur ${sensor.id}:`, error);
            }
        }
    }
    
    // Recharger les capteurs pour afficher les nouvelles valeurs
    if (typeof loadSensors === 'function') {
        await loadSensors();
    }
    
    // Recharger la grille
    if (typeof displayHouseGrid === 'function') {
        displayHouseGrid();
    }
    
    // Déclencher l'automatisation pour appliquer les règles (mode silencieux)
    if (typeof triggerAutomation === 'function') {
        await triggerAutomation(true);
    }
}

/**
 * Nettoyer l'intervalle au déchargement
 */
window.addEventListener('beforeunload', () => {
    if (weatherUpdateInterval) {
        clearInterval(weatherUpdateInterval);
    }
});
