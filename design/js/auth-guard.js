/**
 * Auth Guard - Protection des pages
 * 
 * Ce script doit être inclus en haut de chaque page protégée (dashboard, config-scan, etc.)
 * Il vérifie que l'utilisateur est connecté, sinon redirige vers login.html
 */

// Vérifier l'authentification immédiatement
(async function() {
    // Vérifier si authManager existe (chargé depuis auth.js)
    if (typeof authManager === 'undefined') {
        console.error('AuthManager non chargé ! Assurez-vous que auth.js est inclus avant auth-guard.js');
        window.location.href = 'login.html';
        return;
    }

    // Vérifier si l'utilisateur est connecté
    if (!authManager.isAuthenticated()) {
        console.log('Utilisateur non authentifié, redirection vers login...');
        window.location.href = 'login.html';
        return;
    }

    // ✅ Vérifier la validité du token en appelant l'API
    const isValid = await authManager.validateToken();
    if (!isValid) {
        console.log('🔒 Token invalide ou expiré, redirection vers login...');
        window.location.href = 'login.html';
        return;
    }

    console.log('✅ Utilisateur authentifié:', authManager.user);
})();

/**
 * Fonction pour afficher les infos utilisateur dans la navbar
 * Appeler cette fonction après le chargement du DOM
 */
function displayUserInfo() {
    const user = authManager.getUser();
    
    if (!user) return;

    // Chercher les éléments où afficher les infos
    const userNameElement = document.getElementById('user-name');
    const userEmailElement = document.getElementById('user-email');
    const userCompanyElement = document.getElementById('user-company');

    if (userNameElement) {
        userNameElement.textContent = user.full_name || user.email;
    }

    if (userEmailElement) {
        userEmailElement.textContent = user.email;
    }

    if (userCompanyElement && user.company_name) {
        userCompanyElement.textContent = user.company_name;
    }
}

/**
 * Fonction pour ajouter un bouton de déconnexion
 * Appeler cette fonction après le chargement du DOM
 */
function setupLogoutButton() {
    const logoutButton = document.getElementById('logout-button');
    
    if (logoutButton) {
        logoutButton.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Confirmer la déconnexion
            if (confirm('Voulez-vous vraiment vous déconnecter ?')) {
                authManager.logout();
            }
        });
    }
}

/**
 * Rafraîchit les informations utilisateur depuis l'API
 * Cette fonction est appelée au chargement de chaque page pour s'assurer
 * que les infos affichées sont à jour
 */
async function refreshUserInfo() {
    if (!authManager) return;

    // Récupérer les infos à jour depuis l'API
    const result = await authManager.getCurrentUser();

    if (result.success) {
        // Mettre à jour l'affichage
        displayUserInfo();

        // Mettre à jour le menu utilisateur si présent
        if (window.userMenu) {
            window.userMenu.user = result.user;
            window.userMenu.updateUserInfo();
        }
    }
}

// Auto-setup au chargement du DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
        await refreshUserInfo();  // ✅ RAFRAÎCHIR LES INFOS DEPUIS L'API
        displayUserInfo();
        setupLogoutButton();
    });
} else {
    (async () => {
        await refreshUserInfo();  // ✅ RAFRAÎCHIR LES INFOS DEPUIS L'API
        displayUserInfo();
        setupLogoutButton();
    })();
}

