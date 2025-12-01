/**
 * Configuration d'environnement pour CloudDiagnoze Frontend
 * 
 * ✅ SÉCURITÉ : Ce fichier centralise toutes les URLs et configurations
 * qui varient selon l'environnement (dev, staging, production)
 * 
 * INSTRUCTIONS :
 * 1. En développement : Utiliser les URLs localhost
 * 2. En production : Remplacer par vos URLs de production (HTTPS)
 * 3. Ne jamais commiter les URLs de production dans Git
 */

// Détection automatique de l'environnement
const ENV = {
    // Détecte si on est en local ou en production
    isDevelopment: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    isProduction: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
};

// Configuration des URLs selon l'environnement
const ENV_CONFIG = {
    development: {
        API_BASE_URL: 'http://localhost:8000/api/v1',
        AUTH_API_BASE_URL: 'http://localhost:8000/api/v1/auth'
    },
    production: {
        // ⚠️ À REMPLACER par vos URLs de production (HTTPS obligatoire)
        API_BASE_URL: 'https://api.votre-domaine.com/api/v1',
        AUTH_API_BASE_URL: 'https://api.votre-domaine.com/api/v1/auth'
    }
};

// Sélection de la configuration selon l'environnement
const CURRENT_ENV = ENV.isDevelopment ? 'development' : 'production';
const CONFIG = ENV_CONFIG[CURRENT_ENV];

// Export des URLs pour utilisation dans les autres fichiers
window.API_BASE_URL = CONFIG.API_BASE_URL;
window.AUTH_API_BASE_URL = CONFIG.AUTH_API_BASE_URL;

// Log de l'environnement détecté (utile pour debug)
console.log(`🌍 Environnement détecté : ${CURRENT_ENV}`);
console.log(`🔗 API Base URL : ${CONFIG.API_BASE_URL}`);
console.log(`🔐 Auth API URL : ${CONFIG.AUTH_API_BASE_URL}`);

