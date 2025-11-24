/**
 * Classe pour gérer la configuration et le lancement des scans
 */
class ConfigScan {
    constructor() {
        this.selectedServices = []; // Services sélectionnés par défaut (vide au départ)
        this.selectedRegions = []; // Régions sélectionnées
        this.allRegions = [
            'us-east-1',
            'us-east-2',
            'us-west-1',
            'us-west-2',
            'eu-west-1',
            'eu-west-2',
            'eu-west-3',
            'eu-central-1',
            'ap-southeast-1',
            'ap-southeast-2',
            'ap-northeast-1',
            'ap-northeast-2',
            'sa-east-1',
            'ca-central-1'
        ];
        this.currentScanId = null;
        this.scanInterval = null;
    }

    /**
     * Initialise la page
     */
    async init() {
        console.log('🚀 Initialisation Config Scan...');
        
        // Remplir la liste des régions
        this.renderRegionsList();
        
        // Charger l'historique des scans
        await this.loadScanHistory();
        
        console.log('✅ Config Scan initialisé');
    }

    /**
     * Affiche la liste des régions AWS
     */
    renderRegionsList() {
        const container = document.getElementById('regions-list');
        if (!container) return;

        container.innerHTML = '';

        this.allRegions.forEach(region => {
            const div = document.createElement('div');
            div.className = 'flex items-center gap-2';
            div.innerHTML = `
                <input type="checkbox" 
                       id="region-${region}" 
                       class="toggle-checkbox w-4 h-4 rounded" 
                       value="${region}"
                       onchange="configScan.toggleRegion('${region}', this.checked)"/>
                <label for="region-${region}" class="text-slate-300 text-sm cursor-pointer">${region}</label>
            `;
            container.appendChild(div);
        });
    }

    /**
     * Toggle un service
     */
    toggleService(service) {
        const card = document.querySelector(`[data-service="${service}"]`);
        const checkbox = document.querySelector(`[data-service-toggle="${service}"]`);

        if (!card || !checkbox || checkbox.disabled) return;

        // Vérifier si le service est déjà dans la liste (source de vérité)
        const isSelected = this.selectedServices.includes(service);

        if (isSelected) {
            // Désactiver
            card.classList.remove('selected');
            checkbox.checked = false;
            this.selectedServices = this.selectedServices.filter(s => s !== service);
        } else {
            // Activer
            card.classList.add('selected');
            checkbox.checked = true;
            // Ajouter uniquement si pas déjà présent (évite les doublons)
            if (!this.selectedServices.includes(service)) {
                this.selectedServices.push(service);
            }
        }

        console.log('Services sélectionnés:', this.selectedServices);
    }

    /**
     * Toggle une région
     */
    toggleRegion(region, checked) {
        if (checked) {
            if (!this.selectedRegions.includes(region)) {
                this.selectedRegions.push(region);
            }
        } else {
            this.selectedRegions = this.selectedRegions.filter(r => r !== region);
            // Décocher "Toutes les régions" si une région est décochée
            document.getElementById('all-regions').checked = false;
        }

        console.log('Régions sélectionnées:', this.selectedRegions);
    }

    /**
     * Toggle toutes les régions
     */
    toggleAllRegions(checked) {
        const checkboxes = document.querySelectorAll('#regions-list input[type="checkbox"]');
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });

        if (checked) {
            this.selectedRegions = [...this.allRegions];
        } else {
            this.selectedRegions = [];
        }

        console.log('Régions sélectionnées:', this.selectedRegions);
    }

    /**
     * Lance un scan
     */
    async startScan() {
        // Validation
        if (this.selectedServices.length === 0) {
            this.showNotification('Veuillez sélectionner au moins un service', 'error');
            return;
        }

        if (this.selectedRegions.length === 0) {
            this.showNotification('Veuillez sélectionner au moins une région', 'error');
            return;
        }

        // ✅ VÉRIFIER QUE LE ROLE ARN EST CONFIGURÉ
        try {
            const result = await authManager.getCurrentUser();
            if (!result.success || !result.user.role_arn) {
                this.showNotification(
                    '⚠️ Veuillez configurer votre AWS Role ARN dans les paramètres avant de lancer un scan.',
                    'error'
                );
                // Rediriger vers la page de paramètres après 2 secondes
                setTimeout(() => {
                    window.location.href = 'settings.html';
                }, 2000);
                return;
            }
            this.userRoleArn = result.user.role_arn;
        } catch (error) {
            console.error('❌ Erreur lors de la récupération du role ARN:', error);
            this.showNotification('Erreur lors de la récupération de votre configuration AWS', 'error');
            return;
        }

        console.log('🚀 Lancement du scan...');
        console.log('Services:', this.selectedServices);
        console.log('Régions:', this.selectedRegions);
        console.log('Role ARN:', this.userRoleArn);

        try {
            // Désactiver le bouton de scan
            const scanButton = document.querySelector('button[onclick="configScan.startScan()"]');
            if (scanButton) {
                scanButton.disabled = true;
                scanButton.classList.add('opacity-50', 'cursor-not-allowed');
            }

            // Afficher les barres de progression pour chaque service sélectionné
            this.selectedServices.forEach(service => {
                this.showServiceProgress(service);
            });

            // ✅ LANCER UN SEUL SCAN AVEC TOUS LES SERVICES (au lieu de plusieurs scans séparés)
            // Cela garantit que tous les services auront le même timestamp et seront groupés dans la même session
            await this.scanAllServices(this.selectedServices);

            // Marquer tous les services comme complétés
            this.selectedServices.forEach(service => {
                this.completeServiceProgress(service);
            });

            // Attendre 2 secondes pour montrer le succès
            await new Promise(resolve => setTimeout(resolve, 2000));

            // Cacher les barres de progression
            this.selectedServices.forEach(service => {
                this.hideServiceProgress(service);
            });

            // Recharger l'historique
            await this.loadScanHistory();

            // Réactiver le bouton
            if (scanButton) {
                scanButton.disabled = false;
                scanButton.classList.remove('opacity-50', 'cursor-not-allowed');
            }

            // Notification avec redirection vers dashboard
            this.showSuccessNotificationWithRedirect();

        } catch (error) {
            console.error('❌ Erreur lors du scan:', error);
            this.showNotification('Erreur lors du scan: ' + error.message, 'error');

            // Marquer les services en erreur
            this.selectedServices.forEach(service => {
                this.errorServiceProgress(service);
            });

            // Réactiver le bouton
            const scanButton = document.querySelector('button[onclick="configScan.startScan()"]');
            if (scanButton) {
                scanButton.disabled = false;
                scanButton.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        }
    }

    /**
     * Lance un scan avec TOUS les services sélectionnés en une seule requête
     * Cela garantit que tous les services auront le même timestamp et seront groupés dans la même session
     */
    async scanAllServices(services) {
        console.log(`📡 Scan de ${services.length} service(s): ${services.join(', ').toUpperCase()}...`);

        // ✅ LANCER UN SEUL SCAN AVEC TOUS LES SERVICES
        const scanRequest = {
            provider: 'aws',
            services: services,  // ✅ Tous les services en une seule requête
            auth_mode: {
                type: 'sts',
                role_arn: this.userRoleArn
            },
            client_id: 'ASM-Enterprise',
            regions: this.selectedRegions
        };

        try {
            // Démarrer la simulation de progression pour tous les services
            const progressPromises = services.map(service =>
                this.simulateServiceProgress(service)
            );

            // Appeler l'API avec le token JWT
            const response = await fetch(`${API_CONFIG.BASE_URL}/scans`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authManager.getToken()}`
                },
                body: JSON.stringify(scanRequest)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log(`✅ Scan multi-services lancé:`, data);

            // Attendre que toutes les progressions soient terminées
            await Promise.all(progressPromises);

        } catch (error) {
            console.error(`❌ Erreur scan multi-services:`, error);
            throw error;
        }
    }

    /**
     * Scanne un service spécifique (conservé pour compatibilité)
     * @deprecated Utiliser scanAllServices à la place
     */
    async scanService(service) {
        return this.scanAllServices([service]);
    }

    /**
     * Affiche la barre de progression pour un service
     */
    showServiceProgress(service) {
        const progressDiv = document.querySelector(`[data-service-progress="${service}"]`);
        const serviceCard = document.querySelector(`[data-service="${service}"]`);

        if (progressDiv) {
            progressDiv.classList.remove('hidden');
            // Réinitialiser la progression
            this.updateServiceProgress(service, 0, 0);
        }

        if (serviceCard) {
            serviceCard.classList.add('scanning');
        }
    }

    /**
     * Cache la barre de progression pour un service
     */
    hideServiceProgress(service) {
        const progressDiv = document.querySelector(`[data-service-progress="${service}"]`);
        const serviceCard = document.querySelector(`[data-service="${service}"]`);

        if (progressDiv) {
            progressDiv.classList.add('hidden');
        }

        if (serviceCard) {
            serviceCard.classList.remove('scanning');
        }
    }

    /**
     * Met à jour la progression d'un service
     */
    updateServiceProgress(service, percentage, resourcesCount) {
        const progressDiv = document.querySelector(`[data-service-progress="${service}"]`);
        if (!progressDiv) return;

        const progressBar = progressDiv.querySelector('.scan-progress-bar');
        const percentageText = progressDiv.querySelector('.scan-percentage');
        const resourcesText = progressDiv.querySelector('.scan-resources-count');

        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
        if (percentageText) {
            percentageText.textContent = `${percentage}%`;
        }
        if (resourcesText) {
            resourcesText.textContent = `${resourcesCount} ressource${resourcesCount > 1 ? 's' : ''} trouvée${resourcesCount > 1 ? 's' : ''}`;
        }
    }

    /**
     * Marque un service comme complété
     */
    completeServiceProgress(service) {
        const progressDiv = document.querySelector(`[data-service-progress="${service}"]`);
        const serviceCard = document.querySelector(`[data-service="${service}"]`);

        if (!progressDiv) return;

        const statusText = progressDiv.querySelector('.scan-status-text');
        const spinner = progressDiv.querySelector('.material-symbols-outlined');
        const resourcesText = progressDiv.querySelector('.scan-resources-count');

        // Extraire le nombre de ressources actuel
        const currentText = resourcesText ? resourcesText.textContent : '0 ressources trouvées';
        const currentResources = parseInt(currentText.match(/\d+/)?.[0] || '0');

        // Mettre à jour à 100%
        this.updateServiceProgress(service, 100, currentResources);

        if (statusText) {
            statusText.textContent = '✓ Scan terminé';
            statusText.classList.add('text-green-400');
        }
        if (spinner) {
            spinner.classList.remove('animate-spin');
            spinner.textContent = 'check_circle';
            spinner.classList.add('text-green-400');
        }

        // Retirer l'animation de scanning
        if (serviceCard) {
            serviceCard.classList.remove('scanning');
        }
    }

    /**
     * Marque un service en erreur
     */
    errorServiceProgress(service) {
        const progressDiv = document.querySelector(`[data-service-progress="${service}"]`);
        if (!progressDiv) return;

        const statusText = progressDiv.querySelector('.scan-status-text');
        const spinner = progressDiv.querySelector('.material-symbols-outlined');
        const progressBar = progressDiv.querySelector('.scan-progress-bar');

        if (statusText) {
            statusText.textContent = '✗ Erreur';
            statusText.classList.add('text-red-400');
        }
        if (spinner) {
            spinner.classList.remove('animate-spin');
            spinner.textContent = 'error';
            spinner.classList.add('text-red-400');
        }
        if (progressBar) {
            progressBar.classList.remove('from-blue-500', 'to-blue-400', 'from-green-500', 'to-green-400', 'from-orange-500', 'to-orange-400', 'from-cyan-500', 'to-cyan-400');
            progressBar.classList.add('from-red-500', 'to-red-400');
        }
    }

    /**
     * Simule la progression du scan pour un service spécifique
     */
    async simulateServiceProgress(service) {
        return new Promise((resolve) => {
            let progress = 0;
            let resources = 0;

            const interval = setInterval(() => {
                // Augmenter la progression de manière aléatoire
                progress += Math.floor(Math.random() * 15) + 5;
                if (progress > 95) progress = 95; // Ne pas atteindre 100% avant la fin

                // Augmenter le nombre de ressources
                resources += Math.floor(Math.random() * 3) + 1;

                // Mettre à jour l'affichage
                this.updateServiceProgress(service, progress, resources);
            }, 400);

            // Terminer après 3-5 secondes (aléatoire pour chaque service)
            const duration = 3000 + Math.random() * 2000;
            setTimeout(() => {
                clearInterval(interval);
                resolve();
            }, duration);
        });
    }

    /**
     * Affiche le statut du scan
     */
    showScanStatus() {
        const statusDiv = document.getElementById('scan-status');
        if (statusDiv) {
            statusDiv.classList.remove('hidden');
            document.getElementById('resources-found').textContent = '0';
        }
    }

    /**
     * Masque le statut du scan
     */
    hideScanStatus() {
        const statusDiv = document.getElementById('scan-status');
        if (statusDiv) {
            statusDiv.classList.add('hidden');
        }
    }

    /**
     * Charge l'historique des scans
     */
    async loadScanHistory() {
        try {
            const data = await api.getScansHistory({ limit: 20 });
            console.log('📊 Historique des scans:', data);
            this.renderScanHistory(data.scans || []);
        } catch (error) {
            console.error('❌ Erreur chargement historique:', error);
        }
    }

    /**
     * Affiche l'historique des scans - Groupés par scan
     */
    renderScanHistory(scans) {
        const container = document.getElementById('scan-history');
        if (!container) return;

        if (scans.length === 0) {
            container.innerHTML = '<p class="text-slate-400 text-sm text-center py-4">Aucun scan pour le moment</p>';
            return;
        }

        container.innerHTML = '';

        // Grouper les scans par timestamp (scans lancés en même temps)
        const groupedScans = this.groupScansByTimestamp(scans);

        // Afficher les 5 derniers groupes
        groupedScans.slice(0, 5).forEach(scanGroup => {
            const date = new Date(scanGroup.timestamp);
            const formattedDate = date.toLocaleDateString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });

            // Déterminer le statut global
            const hasSuccess = scanGroup.scans.some(s => s.status === 'success');
            const hasFailed = scanGroup.scans.some(s => s.status === 'failed');
            const statusColor = hasFailed ? 'text-red-400' : hasSuccess ? 'text-green-400' : 'text-orange-400';
            const statusText = hasFailed ? 'Partiel' : hasSuccess ? 'Complété' : 'En cours';

            // Calculer le total de ressources
            const totalResources = scanGroup.scans.reduce((sum, s) => sum + (s.total_resources || 0), 0);

            const div = document.createElement('div');
            div.className = 'glass-card rounded-lg p-3 border border-slate-700 hover:border-primary/50 cursor-pointer transition-all';
            div.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center gap-2">
                        <span class="text-slate-400 text-xs font-mono">#${scanGroup.id}</span>
                        <div class="flex gap-1">
                            ${scanGroup.scans.map(s => {
                                const color = s.service_type === 'ec2' ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' :
                                             s.service_type === 's3' ? 'bg-green-500/20 text-green-400 border-green-500/30' :
                                             s.service_type === 'vpc' ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' :
                                             s.service_type === 'rds' ? 'bg-purple-500/20 text-purple-400 border-purple-500/30' :
                                             'bg-purple-500/20 text-purple-400 border-purple-500/30';
                                return `<span class="px-1.5 py-0.5 rounded text-xs font-medium border ${color}">${s.service_type.toUpperCase()}</span>`;
                            }).join('')}
                        </div>
                    </div>
                    <span class="text-xs ${statusColor} font-medium">${statusText}</span>
                </div>
                <div class="flex items-center justify-between text-xs text-slate-400">
                    <span>${formattedDate}</span>
                    <span class="font-semibold text-primary">${totalResources} ressources</span>
                </div>
            `;

            // Ajouter l'événement de clic pour afficher les détails
            div.addEventListener('click', () => this.showScanDetails(scanGroup));

            container.appendChild(div);
        });
    }

    /**
     * Groupe les scans par timestamp (scans lancés en même temps)
     */
    groupScansByTimestamp(scans) {
        // Trier par timestamp décroissant
        const sorted = [...scans].sort((a, b) =>
            new Date(b.scan_timestamp) - new Date(a.scan_timestamp)
        );

        const groups = [];
        const timeThreshold = 60000; // 1 minute en millisecondes

        sorted.forEach(scan => {
            const scanTime = new Date(scan.scan_timestamp).getTime();

            // Chercher un groupe existant avec un timestamp proche
            let group = groups.find(g =>
                Math.abs(new Date(g.timestamp).getTime() - scanTime) < timeThreshold
            );

            if (!group) {
                // Créer un nouveau groupe
                group = {
                    id: scan.scan_id,
                    timestamp: scan.scan_timestamp,
                    scans: []
                };
                groups.push(group);
            }

            group.scans.push(scan);
        });

        return groups;
    }

    /**
     * Affiche les détails d'un scan dans une notification
     */
    showScanDetails(scanGroup) {
        const date = new Date(scanGroup.timestamp);
        const formattedDate = date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        let details = `<div class="space-y-2">`;
        details += `<p class="font-semibold text-white mb-3">Scan #${scanGroup.id} - ${formattedDate}</p>`;

        scanGroup.scans.forEach(scan => {
            const serviceColor = scan.service_type === 'ec2' ? 'text-blue-400' :
                                scan.service_type === 's3' ? 'text-green-400' :
                                scan.service_type === 'vpc' ? 'text-orange-400' :
                                scan.service_type === 'rds' ? 'text-purple-400' : 'text-purple-400';
            const statusColor = scan.status === 'success' ? 'text-green-400' :
                               scan.status === 'failed' ? 'text-red-400' : 'text-orange-400';

            details += `
                <div class="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
                    <div class="flex items-center justify-between mb-1">
                        <span class="font-semibold ${serviceColor}">${scan.service_type.toUpperCase()}</span>
                        <span class="text-xs ${statusColor}">${scan.status}</span>
                    </div>
                    <div class="text-sm text-slate-400">
                        <span>${scan.total_resources || 0} ressources trouvées</span>
                    </div>
                </div>
            `;
        });

        details += `</div>`;

        this.showNotification(details, 'info');
    }

    /**
     * Réinitialise la configuration
     */
    resetConfig() {
        // Réinitialiser les services (tout décocher)
        this.selectedServices = [];
        document.querySelectorAll('.service-card').forEach(card => {
            const checkbox = card.querySelector('input[type="checkbox"]');

            // Décocher tous les services
            card.classList.remove('selected');
            if (checkbox) checkbox.checked = false;
        });

        // Réinitialiser les régions
        this.selectedRegions = [];
        document.querySelectorAll('#regions-list input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        document.getElementById('all-regions').checked = false;

        this.showNotification('Configuration réinitialisée', 'info');
    }

    /**
     * Affiche une notification
     */
    showNotification(message, type = 'info') {
        const colors = {
            success: 'bg-green-500/10 border-green-500 text-green-500',
            error: 'bg-red-500/10 border-red-500 text-red-500',
            info: 'bg-blue-500/10 border-blue-500 text-blue-500'
        };

        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 ${colors[type]} border px-6 py-4 rounded-lg backdrop-blur-sm z-50 animate-fade-in`;
        notification.innerHTML = `
            <div class="flex items-center gap-3">
                <span class="material-symbols-outlined">${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}</span>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    /**
     * Affiche une notification de succès avec bouton de redirection
     */
    showSuccessNotificationWithRedirect() {
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500/10 border border-green-500 text-green-500 px-6 py-4 rounded-lg backdrop-blur-sm z-50 animate-fade-in shadow-lg';
        notification.innerHTML = `
            <div class="flex items-center gap-4">
                <span class="material-symbols-outlined text-3xl">check_circle</span>
                <div class="flex-1">
                    <p class="font-bold text-lg">Scan terminé avec succès !</p>
                    <p class="text-sm text-green-400/80 mt-1">Les résultats sont maintenant disponibles</p>
                </div>
                <button onclick="window.location.href='dashbord.html'"
                        class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-medium transition-colors">
                    Voir le dashboard
                </button>
                <button onclick="this.parentElement.parentElement.remove()"
                        class="text-green-400 hover:text-green-300">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-fermeture après 10 secondes
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 10000);
    }
}

