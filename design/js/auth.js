/**
 * Module d'authentification pour CloudDiagnoze
 * 
 * Gère :
 * - Inscription (signup)
 * - Connexion (login)
 * - Déconnexion (logout)
 * - Récupération des infos utilisateur
 * - Stockage du token JWT
 * - Protection des pages
 */

// Configuration de l'API
const AUTH_API_BASE_URL = 'http://localhost:8000/api/v1/auth';

// Clés de stockage localStorage
const STORAGE_KEYS = {
    TOKEN: 'clouddiagnoze_token',
    USER: 'clouddiagnoze_user'
};

/**
 * Classe principale pour gérer l'authentification
 */
class AuthManager {
    constructor() {
        this.token = this.getToken();
        this.user = this.getUser();
    }

    /**
     * Récupère le token depuis localStorage
     */
    getToken() {
        return localStorage.getItem(STORAGE_KEYS.TOKEN);
    }

    /**
     * Récupère les infos utilisateur depuis localStorage
     */
    getUser() {
        const userJson = localStorage.getItem(STORAGE_KEYS.USER);
        return userJson ? JSON.parse(userJson) : null;
    }

    /**
     * Stocke le token et les infos utilisateur
     */
    setAuth(token, user) {
        localStorage.setItem(STORAGE_KEYS.TOKEN, token);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
        this.token = token;
        this.user = user;
    }

    /**
     * Supprime le token et les infos utilisateur
     */
    clearAuth() {
        localStorage.removeItem(STORAGE_KEYS.TOKEN);
        localStorage.removeItem(STORAGE_KEYS.USER);
        this.token = null;
        this.user = null;
    }

    /**
     * Vérifie si l'utilisateur est connecté
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * Inscription d'un nouvel utilisateur
     */
    async signup(email, password, fullName = null, companyName = null, roleArn = null) {
        try {
            const response = await fetch(`${AUTH_API_BASE_URL}/signup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email,
                    password,
                    full_name: fullName,
                    company_name: companyName,
                    role_arn: roleArn
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Erreur lors de l\'inscription');
            }

            return { success: true, message: data.message };
        } catch (error) {
            console.error('Erreur signup:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Connexion d'un utilisateur
     */
    async login(email, password) {
        try {
            const response = await fetch(`${AUTH_API_BASE_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email,
                    password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Erreur lors de la connexion');
            }

            // Stocker le token et les infos utilisateur
            this.setAuth(data.access_token, data.user);

            return { success: true, user: data.user };
        } catch (error) {
            console.error('Erreur login:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Déconnexion
     */
    logout() {
        this.clearAuth();
        window.location.href = 'login.html';
    }

    /**
     * Récupère les infos de l'utilisateur connecté depuis l'API
     */
    async getCurrentUser() {
        if (!this.token) {
            return { success: false, error: 'Non authentifié' };
        }

        try {
            const response = await fetch(`${AUTH_API_BASE_URL}/me`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            const data = await response.json();

            if (!response.ok) {
                // Token invalide ou expiré
                if (response.status === 401) {
                    this.clearAuth();
                    window.location.href = 'login.html';
                }
                throw new Error(data.detail || 'Erreur lors de la récupération des infos utilisateur');
            }

            // Mettre à jour les infos utilisateur en cache
            localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(data));
            this.user = data;

            return { success: true, user: data };
        } catch (error) {
            console.error('Erreur getCurrentUser:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Demande de réinitialisation de mot de passe
     */
    async forgotPassword(email) {
        try {
            const response = await fetch(`${AUTH_API_BASE_URL}/forgot-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Erreur lors de la demande de réinitialisation');
            }

            return { success: true, message: data.message };
        } catch (error) {
            console.error('Erreur forgotPassword:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Réinitialisation du mot de passe
     */
    async resetPassword(token, newPassword) {
        try {
            const response = await fetch(`${AUTH_API_BASE_URL}/reset-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token,
                    new_password: newPassword
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Erreur lors de la réinitialisation du mot de passe');
            }

            return { success: true, message: data.message };
        } catch (error) {
            console.error('Erreur resetPassword:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Protège une page (redirige vers login si non connecté)
     */
    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = 'login.html';
            return false;
        }
        return true;
    }

    /**
     * Redirige vers le dashboard si déjà connecté (pour login/signup pages)
     */
    redirectIfAuthenticated() {
        if (this.isAuthenticated()) {
            window.location.href = 'dashbord.html';
            return true;
        }
        return false;
    }
}

/**
 * Utilitaires pour l'UI
 */
class AuthUI {
    /**
     * Affiche un message d'erreur
     */
    static showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.classList.remove('hidden');
            element.classList.add('flex');
        }
    }

    /**
     * Cache un message d'erreur
     */
    static hideError(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add('hidden');
            element.classList.remove('flex');
        }
    }

    /**
     * Affiche un message de succès
     */
    static showSuccess(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.classList.remove('hidden');
            element.classList.add('flex');
        }
    }

    /**
     * Active/désactive un bouton
     */
    static setButtonLoading(buttonId, loading, loadingText = 'Chargement...') {
        const button = document.getElementById(buttonId);
        if (button) {
            button.disabled = loading;
            if (loading) {
                button.dataset.originalText = button.textContent;
                button.innerHTML = `
                    <svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    ${loadingText}
                `;
            } else {
                button.textContent = button.dataset.originalText || button.textContent;
            }
        }
    }

    /**
     * Toggle password visibility
     */
    static setupPasswordToggle(inputId, buttonId) {
        const input = document.getElementById(inputId);
        const button = document.getElementById(buttonId);
        
        if (input && button) {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const type = input.type === 'password' ? 'text' : 'password';
                input.type = type;
                
                const icon = button.querySelector('.material-symbols-outlined');
                if (icon) {
                    icon.textContent = type === 'password' ? 'visibility' : 'visibility_off';
                }
            });
        }
    }
}

// Instance globale
window.authManager = new AuthManager();
window.AuthUI = AuthUI;

