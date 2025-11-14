/**
 * Settings Page - Gestion des paramètres utilisateur
 */

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Initialisation de la page Settings...');

    // 1. Vérifier l'authentification
    if (!authManager.isAuthenticated()) {
        console.log('❌ Utilisateur non authentifié, redirection vers login...');
        window.location.href = 'login.html';
        return;
    }

    // 2. Charger les informations utilisateur
    let currentUser = null;
    try {
        const result = await authManager.getCurrentUser();

        if (!result.success) {
            throw new Error(result.error || 'Erreur lors de la récupération des infos utilisateur');
        }

        currentUser = result.user;
        console.log('✅ Utilisateur authentifié:', currentUser);

        // Header
        document.getElementById('user-name-header').textContent = currentUser.full_name || 'Utilisateur';
        document.getElementById('user-email-header').textContent = currentUser.email;

        // Initialiser le menu utilisateur popup
        userMenu.init(currentUser);

        // Remplir le formulaire avec les données actuelles
        populateForm(currentUser);
    } catch (error) {
        console.error('❌ Erreur lors de la récupération des infos utilisateur:', error);
        authManager.logout();
        window.location.href = 'login.html';
        return;
    }

    // 3. Gérer la soumission du formulaire d'informations personnelles
    const personalInfoForm = document.getElementById('personal-info-form');
    personalInfoForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handlePersonalInfoUpdate();
    });

    // 4. Gérer la soumission du formulaire de changement de mot de passe
    const passwordForm = document.getElementById('password-form');
    passwordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handlePasswordChange();
    });

    // 5. Gérer le bouton de suppression des données utilisateur
    const btnClearUserData = document.getElementById('btn-clear-user-data');
    if (btnClearUserData) {
        btnClearUserData.addEventListener('click', async () => {
            await handleClearUserData();
        });
    }
});

/**
 * Remplit le formulaire avec les données utilisateur actuelles
 */
function populateForm(user) {
    document.getElementById('full-name').value = user.full_name || '';
    document.getElementById('email').value = user.email || '';
    document.getElementById('company-name').value = user.company_name || '';
    document.getElementById('role-arn').value = user.role_arn || '';

    // Informations du compte
    if (user.created_at) {
        const createdDate = new Date(user.created_at);
        document.getElementById('account-created').textContent = createdDate.toLocaleDateString('fr-FR');
    }
    if (user.last_login) {
        const lastLoginDate = new Date(user.last_login);
        document.getElementById('last-login').textContent = lastLoginDate.toLocaleDateString('fr-FR');
    }
    document.getElementById('account-status').textContent = user.is_active ? 'Actif' : 'Inactif';
}

/**
 * Gère la mise à jour des informations personnelles
 */
async function handlePersonalInfoUpdate() {
    const fullName = document.getElementById('full-name').value.trim();
    const companyName = document.getElementById('company-name').value.trim();
    const roleArn = document.getElementById('role-arn').value.trim();

    // Validation
    if (!fullName) {
        showNotification('Le nom complet est requis', 'error');
        return;
    }

    try {
        showNotification('Mise à jour en cours...', 'info');

        const response = await fetch(`${API_CONFIG.BASE_URL}/auth/me`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authManager.getToken()}`
            },
            body: JSON.stringify({
                full_name: fullName,
                company_name: companyName,
                role_arn: roleArn
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de la mise à jour');
        }

        const updatedUser = await response.json();
        console.log('✅ Informations mises à jour:', updatedUser);

        // Mettre à jour le localStorage
        localStorage.setItem('clouddiagnoze_user', JSON.stringify(updatedUser));

        // Mettre à jour authManager
        authManager.user = updatedUser;

        // Mettre à jour l'affichage
        const headerName = document.getElementById('user-name-header');
        if (headerName) {
            headerName.textContent = updatedUser.full_name || 'Utilisateur';
        }

        // Mettre à jour le menu utilisateur
        if (window.userMenu) {
            window.userMenu.user = updatedUser;
            window.userMenu.updateUserInfo();
        }

        showNotification('Informations mises à jour avec succès !', 'success');
    } catch (error) {
        console.error('❌ Erreur:', error);
        showNotification(error.message, 'error');
    }
}

/**
 * Gère le changement de mot de passe
 */
async function handlePasswordChange() {
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
        showNotification('Tous les champs sont requis', 'error');
        return;
    }

    if (newPassword !== confirmPassword) {
        showNotification('Les mots de passe ne correspondent pas', 'error');
        return;
    }

    if (newPassword.length < 8) {
        showNotification('Le mot de passe doit contenir au moins 8 caractères', 'error');
        return;
    }

    try {
        showNotification('Changement du mot de passe...', 'info');

        const response = await fetch(`${API_CONFIG.BASE_URL}/auth/change-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authManager.getToken()}`
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors du changement de mot de passe');
        }

        console.log('✅ Mot de passe changé avec succès');

        // Réinitialiser le formulaire
        document.getElementById('password-form').reset();

        showNotification('Mot de passe changé avec succès !', 'success');
    } catch (error) {
        console.error('❌ Erreur:', error);
        showNotification(error.message, 'error');
    }
}

/**
 * Affiche une notification
 */
function showNotification(message, type = 'info') {
    // Supprimer les notifications existantes
    const existingNotif = document.getElementById('notification');
    if (existingNotif) {
        existingNotif.remove();
    }

    // Créer la notification
    const notification = document.createElement('div');
    notification.id = 'notification';
    notification.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-2xl backdrop-blur-xl border transition-all duration-300 transform translate-x-0 opacity-100`;

    // Couleurs selon le type
    let bgColor, borderColor, iconColor, icon;
    switch (type) {
        case 'success':
            bgColor = 'bg-green-500/20';
            borderColor = 'border-green-500/50';
            iconColor = 'text-green-400';
            icon = 'check_circle';
            break;
        case 'error':
            bgColor = 'bg-red-500/20';
            borderColor = 'border-red-500/50';
            iconColor = 'text-red-400';
            icon = 'error';
            break;
        case 'info':
        default:
            bgColor = 'bg-blue-500/20';
            borderColor = 'border-blue-500/50';
            iconColor = 'text-blue-400';
            icon = 'info';
            break;
    }

    notification.className += ` ${bgColor} ${borderColor}`;
    notification.innerHTML = `
        <div class="flex items-center gap-3">
            <span class="material-symbols-outlined ${iconColor}">${icon}</span>
            <p class="text-white font-medium">${message}</p>
        </div>
    `;

    document.body.appendChild(notification);

    // Animer l'entrée
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
        notification.style.opacity = '1';
    }, 10);

    // Supprimer après 4 secondes
    setTimeout(() => {
        notification.style.transform = 'translateX(400px)';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

/**
 * 🧹 Gère la suppression de toutes les données de l'utilisateur (pour testing)
 */
async function handleClearUserData() {
    // Demander une confirmation
    const confirmed = confirm(
        '⚠️ ATTENTION ⚠️\n\n' +
        'Cette action va supprimer TOUTES vos données de scan :\n' +
        '- Tous les scans EC2 et S3\n' +
        '- Toutes les instances EC2\n' +
        '- Tous les buckets S3\n' +
        '- Toutes les métriques de performance\n' +
        '- Tout l\'historique des scans\n\n' +
        'Votre compte utilisateur sera conservé.\n\n' +
        'Cette action est IRRÉVERSIBLE !\n\n' +
        'Voulez-vous vraiment continuer ?'
    );

    if (!confirmed) {
        return;
    }

    // Demander une double confirmation
    const doubleConfirmed = confirm(
        '🚨 DERNIÈRE CONFIRMATION 🚨\n\n' +
        'Êtes-vous ABSOLUMENT SÛR de vouloir supprimer toutes vos données ?\n\n' +
        'Cliquez sur OK pour confirmer la suppression définitive.'
    );

    if (!doubleConfirmed) {
        return;
    }

    try {
        showNotification('Suppression en cours...', 'info');

        // Appeler l'API pour supprimer les données
        const result = await api.clearUserData();

        console.log('✅ Données supprimées:', result);

        // Afficher le résultat
        showNotification(
            `✅ ${result.deleted.total} éléments supprimés avec succès !\n` +
            `Scans: ${result.deleted.scan_runs}, ` +
            `EC2: ${result.deleted.ec2_instances}, ` +
            `S3: ${result.deleted.s3_buckets}`,
            'success'
        );

        // Recharger la page après 2 secondes
        setTimeout(() => {
            window.location.reload();
        }, 2000);

    } catch (error) {
        console.error('❌ Erreur lors de la suppression:', error);
        showNotification('❌ Erreur lors de la suppression des données', 'error');
    }
}

