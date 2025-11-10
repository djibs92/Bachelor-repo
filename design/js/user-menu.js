/**
 * UserMenu - Composant de menu utilisateur avec popup
 * Gère l'affichage des informations utilisateur et les actions (Configuration, Déconnexion)
 */

class UserMenu {
    constructor() {
        this.isOpen = false;
        this.popupElement = null;
        this.triggerElement = null;
    }

    /**
     * Initialise le menu utilisateur
     * @param {Object} user - Objet utilisateur avec full_name, email, company_name
     */
    init(user) {
        // Éviter les initialisations multiples
        if (this.initialized) {
            this.user = user;
            this.updateUserInfo();
            return;
        }

        this.user = user;
        this.createPopup();
        this.attachEventListeners();
        this.updateUserInfo();
        this.initialized = true;
    }

    /**
     * Crée le HTML du popup
     */
    createPopup() {
        // Vérifier si le popup existe déjà
        if (this.popupElement && this.backdropElement) {
            return; // Déjà créé, on ne recrée pas
        }

        // Créer le backdrop
        const backdrop = document.createElement('div');
        backdrop.id = 'user-menu-backdrop';
        backdrop.className = 'fixed inset-0 bg-black/20 backdrop-blur-sm z-40 hidden opacity-0 transition-opacity duration-300';
        backdrop.addEventListener('click', () => this.close());

        // Créer le popup
        const popup = document.createElement('div');
        popup.id = 'user-menu-popup';
        popup.className = 'fixed top-20 right-8 z-50 hidden opacity-0 scale-95 transition-all duration-300 ease-out';
        popup.innerHTML = `
            <div class="glass-card rounded-xl shadow-2xl border border-slate-700/50 min-w-[280px] overflow-hidden">
                <!-- Header avec infos utilisateur -->
                <div class="bg-gradient-to-r from-blue-500/20 to-purple-500/20 p-4 border-b border-slate-700/50">
                    <div class="flex items-center gap-3">
                        <div class="bg-blue-500/30 rounded-full p-3">
                            <span class="material-symbols-outlined text-blue-400 text-2xl">person</span>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p id="popup-user-name" class="text-white text-sm font-bold truncate">Chargement...</p>
                            <p id="popup-user-email" class="text-slate-300 text-xs truncate">...</p>
                        </div>
                    </div>
                    <div class="mt-3 flex items-center gap-2 text-slate-300 text-xs">
                        <span class="material-symbols-outlined text-xs">business</span>
                        <p id="popup-user-company" class="truncate">...</p>
                    </div>
                </div>

                <!-- Menu Actions -->
                <div class="p-2">
                    <a href="settings.html" class="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-blue-500/20 hover:text-blue-400 transition-all duration-200 group">
                        <span class="material-symbols-outlined text-xl group-hover:scale-110 transition-transform">settings</span>
                        <div class="flex-1">
                            <p class="text-sm font-medium">Configuration</p>
                            <p class="text-xs text-slate-400">Gérer votre compte</p>
                        </div>
                        <span class="material-symbols-outlined text-sm opacity-0 group-hover:opacity-100 transition-opacity">chevron_right</span>
                    </a>
                    
                    <button id="popup-logout-btn" class="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-red-500/20 hover:text-red-400 transition-all duration-200 group">
                        <span class="material-symbols-outlined text-xl group-hover:scale-110 transition-transform">logout</span>
                        <div class="flex-1 text-left">
                            <p class="text-sm font-medium">Déconnexion</p>
                            <p class="text-xs text-slate-400">Se déconnecter du compte</p>
                        </div>
                        <span class="material-symbols-outlined text-sm opacity-0 group-hover:opacity-100 transition-opacity">chevron_right</span>
                    </button>
                </div>
            </div>
        `;

        // Ajouter au DOM
        document.body.appendChild(backdrop);
        document.body.appendChild(popup);

        this.popupElement = popup;
        this.backdropElement = backdrop;
    }

    /**
     * Attache les event listeners
     */
    attachEventListeners() {
        // Trigger button (header user info)
        this.triggerElement = document.getElementById('user-info-header');
        if (this.triggerElement) {
            this.triggerElement.classList.add('cursor-pointer', 'hover:bg-slate-700/50', 'transition-colors');
            this.triggerElement.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggle();
            });
        }

        // Logout button
        const logoutBtn = document.getElementById('popup-logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }

        // Fermer avec Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    /**
     * Met à jour les informations utilisateur dans le popup
     */
    updateUserInfo() {
        if (!this.user) return;

        document.getElementById('popup-user-name').textContent = this.user.full_name || 'Utilisateur';
        document.getElementById('popup-user-email').textContent = this.user.email || '';
        document.getElementById('popup-user-company').textContent = this.user.company_name || 'Aucune entreprise';

        // Mettre à jour aussi le header
        const headerName = document.getElementById('user-name-header');
        if (headerName) {
            headerName.textContent = this.user.full_name || 'Utilisateur';
        }
    }

    /**
     * Rafraîchit les informations utilisateur depuis l'API
     */
    async refresh() {
        if (!authManager) return;

        const result = await authManager.getCurrentUser();
        if (result.success) {
            this.user = result.user;
            this.updateUserInfo();
        }
    }

    /**
     * Ouvre le popup avec animation
     */
    open() {
        this.isOpen = true;

        // Afficher les éléments
        this.backdropElement.classList.remove('hidden');
        this.popupElement.classList.remove('hidden');

        // Forcer un reflow pour l'animation
        this.backdropElement.offsetHeight;
        this.popupElement.offsetHeight;

        // Animer
        requestAnimationFrame(() => {
            this.backdropElement.classList.remove('opacity-0');
            this.backdropElement.classList.add('opacity-100');
            
            this.popupElement.classList.remove('opacity-0', 'scale-95');
            this.popupElement.classList.add('opacity-100', 'scale-100');
        });
    }

    /**
     * Ferme le popup avec animation
     */
    close() {
        this.isOpen = false;

        // Animer la fermeture
        this.backdropElement.classList.remove('opacity-100');
        this.backdropElement.classList.add('opacity-0');
        
        this.popupElement.classList.remove('opacity-100', 'scale-100');
        this.popupElement.classList.add('opacity-0', 'scale-95');

        // Cacher après l'animation
        setTimeout(() => {
            this.backdropElement.classList.add('hidden');
            this.popupElement.classList.add('hidden');
        }, 300);
    }

    /**
     * Toggle le popup
     */
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    /**
     * Gère la déconnexion
     */
    handleLogout() {
        if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
            authManager.logout();
            window.location.href = 'login.html';
        }
    }
}

// Instance globale
window.userMenu = new UserMenu();

