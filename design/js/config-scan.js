/**
 * Classe pour gérer la configuration et le lancement des scans
 */
class ConfigScan {
    constructor() {
        this.selectedServices = []; // Services sélectionnés par défaut (vide au départ)
        this.selectedRegions = []; // Régions sélectionnées
        this.regionGroups = {
            'US East': ['us-east-1', 'us-east-2'],
            'US West': ['us-west-1', 'us-west-2'],
            'Europe': ['eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1'],
            'Asia Pacific': ['ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2'],
            'Other': ['sa-east-1', 'ca-central-1']
        };
        this.allRegions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2',
            'sa-east-1', 'ca-central-1'
        ];
        this.currentScanId = null;
        this.scanInterval = null;
        this.pollingInterval = null;
        this.scannedServices = [];
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
     * Affiche la liste des régions AWS groupées par zone géographique
     */
    renderRegionsList() {
        const container = document.getElementById('regions-list');
        if (!container) return;

        container.innerHTML = '';

        // Créer une grille de cartes pour chaque groupe
        const mainGrid = document.createElement('div');
        mainGrid.className = 'grid grid-cols-1 md:grid-cols-2 gap-4';

        // Pour chaque groupe de régions
        Object.entries(this.regionGroups).forEach(([groupName, regions]) => {
            // Créer la carte du groupe
            const groupCard = document.createElement('div');
            groupCard.className = 'bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700/50 hover:border-primary/30 transition-all duration-300';

            // En-tête du groupe avec icône
            const header = document.createElement('div');
            header.className = 'flex items-center justify-between mb-3 pb-2 border-b border-slate-700/50';

            const titleSection = document.createElement('div');
            titleSection.className = 'flex items-center gap-2';

            // Icône selon la région
            let icon = 'public';
            if (groupName.includes('US')) icon = 'flag';
            else if (groupName.includes('Europe')) icon = 'euro';
            else if (groupName.includes('Asia')) icon = 'language';
            else icon = 'travel_explore';

            titleSection.innerHTML = `
                <span class="material-symbols-outlined text-primary text-lg">${icon}</span>
                <span class="text-slate-100 font-semibold text-sm">${groupName}</span>
                <span class="text-slate-500 text-xs">(${regions.length})</span>
            `;

            // Bouton "Tout sélectionner" pour ce groupe
            const selectAllBtn = document.createElement('button');
            selectAllBtn.className = 'text-xs text-primary hover:text-primary-light transition-colors';
            selectAllBtn.textContent = 'Tout';
            selectAllBtn.onclick = (e) => {
                e.preventDefault();
                const checkboxes = groupCard.querySelectorAll('input[type="checkbox"]');
                const allChecked = Array.from(checkboxes).every(cb => cb.checked);
                checkboxes.forEach(cb => {
                    cb.checked = !allChecked;
                    this.toggleRegion(cb.value, cb.checked);
                });
            };

            header.appendChild(titleSection);
            header.appendChild(selectAllBtn);
            groupCard.appendChild(header);

            // Liste des régions
            const regionsList = document.createElement('div');
            regionsList.className = 'space-y-2';

            regions.forEach(region => {
                const regionItem = document.createElement('label');
                regionItem.className = 'flex items-center gap-3 p-2 rounded-lg hover:bg-slate-700/30 cursor-pointer transition-all group';

                regionItem.innerHTML = `
                    <input type="checkbox"
                           id="region-${region}"
                           class="w-4 h-4 rounded border-slate-600 text-primary focus:ring-2 focus:ring-primary/50 focus:ring-offset-0 cursor-pointer"
                           value="${region}"
                           onchange="configScan.toggleRegion('${region}', this.checked)"/>
                    <span class="text-slate-300 text-sm group-hover:text-slate-100 transition-colors flex-1">${region}</span>
                    <span class="material-symbols-outlined text-slate-600 text-sm group-hover:text-primary transition-colors">location_on</span>
                `;

                regionsList.appendChild(regionItem);
            });

            groupCard.appendChild(regionsList);
            mainGrid.appendChild(groupCard);
        });

        container.appendChild(mainGrid);
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

            // ✅ LANCER UN SEUL SCAN AVEC TOUS LES SERVICES
            // Le polling gérera automatiquement la progression et la redirection
            await this.scanAllServices(this.selectedServices);

            // Le reste est géré par le polling (startScanPolling)

        } catch (error) {
            console.error('❌ Erreur lors du scan:', error);
            this.showNotification('Erreur lors du scan: ' + error.message, 'error');

            // Arrêter le polling
            this.stopScanPolling();

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
            // Appeler l'API (JWT transmis via cookie httpOnly)
            const response = await fetch(`${API_CONFIG.BASE_URL}/scans`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(scanRequest)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log(`✅ Scan multi-services lancé:`, data);

            // Sauvegarder les services scannés pour le polling
            this.scannedServices = services;

            // ✅ Démarrer le polling IMMÉDIATEMENT (pas d'attente)
            this.startScanPolling(services);

        } catch (error) {
            console.error(`❌ Erreur scan multi-services:`, error);
            throw error;
        }
    }

    /**
     * Démarre le polling pour vérifier l'état du scan
     * ✅ OPTIMISÉ : Progression artificielle fluide + vérification backend
     */
    startScanPolling(services) {
        console.log('🔄 Démarrage du polling pour vérifier l\'état du scan...');

        let pollCount = 0;
        const maxPolls = 240; // Maximum 2 minutes (240 * 500ms)
        const progressPerService = {}; // Suivre la progression de chaque service
        const artificialProgressIntervals = {}; // Intervalles pour la progression artificielle

        // Initialiser la progression à 10% pour chaque service
        services.forEach(service => {
            progressPerService[service] = 10;
            this.updateServiceProgress(service, 10, 0);
            console.log(`🎯 Initialisation progression ${service.toUpperCase()}: 10%`);

            // ✨ PROGRESSION ARTIFICIELLE : Monter graduellement de 10% à 70% sur 4 secondes
            let artificialProgress = 10;
            artificialProgressIntervals[service] = setInterval(() => {
                // Si le service n'est pas encore terminé et qu'on est en dessous de 70%
                if (progressPerService[service] < 70 && progressPerService[service] < 100) {
                    artificialProgress += 3; // +3% toutes les 200ms = 70% en ~4 secondes
                    if (artificialProgress <= 70) {
                        progressPerService[service] = artificialProgress;
                        this.updateServiceProgress(service, artificialProgress, 0);
                        console.log(`🎨 Progression artificielle ${service.toUpperCase()}: ${artificialProgress}%`);
                    }
                }
            }, 200); // Toutes les 200ms pour une animation fluide
        });

        // Nettoyer l'ancien polling s'il existe
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        this.pollingInterval = setInterval(async () => {
            pollCount++;
            console.log(`🔄 Poll #${pollCount} - Vérification du statut...`);

            try {
                const status = await api.getScanStatus(services);
                console.log(`📊 Statut du scan (poll #${pollCount}):`, status);

                // Mettre à jour les barres de progression avec les vraies données
                Object.entries(status.services_status).forEach(([service, serviceStatus]) => {
                    if (serviceStatus.completed) {
                        // ✅ Service terminé : Arrêter la progression artificielle et passer à 100%
                        if (artificialProgressIntervals[service]) {
                            clearInterval(artificialProgressIntervals[service]);
                            delete artificialProgressIntervals[service];
                        }

                        console.log(`✅ ${service.toUpperCase()} terminé: ${serviceStatus.total_resources} ressources`);

                        // Progression finale : 70% → 100% en douceur
                        const currentProgress = progressPerService[service];
                        if (currentProgress < 100) {
                            // Animation de 70% à 100% sur 500ms
                            let step = currentProgress;
                            const increment = (100 - currentProgress) / 5; // 5 étapes
                            const finalAnimation = setInterval(() => {
                                step += increment;
                                if (step >= 100) {
                                    step = 100;
                                    clearInterval(finalAnimation);
                                    this.completeServiceProgress(service);
                                }
                                progressPerService[service] = step;
                                this.updateServiceProgress(service, step, serviceStatus.total_resources);
                            }, 100); // Toutes les 100ms
                        } else {
                            progressPerService[service] = 100;
                            this.updateServiceProgress(service, 100, serviceStatus.total_resources);
                            this.completeServiceProgress(service);
                        }
                    } else {
                        // Service en cours : Laisser la progression artificielle faire son travail
                        // Mais si on dépasse 70%, on peut continuer à monter lentement jusqu'à 85%
                        if (progressPerService[service] >= 70 && progressPerService[service] < 85) {
                            progressPerService[service] = Math.min(85, progressPerService[service] + 2);
                            this.updateServiceProgress(service, progressPerService[service], 0);
                        }
                    }
                });

                // Si tous les services sont terminés
                if (status.completed) {
                    console.log('✅ Tous les services ont terminé leur scan !');

                    // Nettoyer tous les intervalles
                    clearInterval(this.pollingInterval);
                    this.pollingInterval = null;
                    Object.values(artificialProgressIntervals).forEach(interval => clearInterval(interval));

                    // Afficher notification de succès
                    this.showNotification('Scan terminé avec succès ! Redirection vers le dashboard...', 'success');

                    // Attendre 2 secondes puis rediriger
                    setTimeout(() => {
                        window.location.href = 'dashboard.html';
                    }, 2000);
                }

                // Timeout après 2 minutes
                if (pollCount >= maxPolls) {
                    console.warn('⚠️ Timeout du polling après 2 minutes');
                    clearInterval(this.pollingInterval);
                    this.pollingInterval = null;
                    Object.values(artificialProgressIntervals).forEach(interval => clearInterval(interval));
                    this.showNotification('Le scan prend plus de temps que prévu. Vérifiez le dashboard.', 'warning');
                }

            } catch (error) {
                console.error('❌ Erreur lors du polling:', error);
            }
        }, 500); // Vérifier toutes les 500ms
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
        const serviceCard = document.querySelector(`[data-service="${service}"]`);
        const progressOverlay = document.querySelector(`[data-progress-overlay="${service}"]`);
        const progressBadge = document.querySelector(`[data-progress-badge="${service}"]`);

        if (serviceCard) {
            serviceCard.classList.add('scanning');
            console.log(`🎯 Carte ${service.toUpperCase()} en mode scanning`);
        }

        // Réinitialiser l'overlay et le badge
        if (progressOverlay) {
            progressOverlay.style.width = '0%';
        }
        if (progressBadge) {
            progressBadge.textContent = '0%';
        }
    }

    /**
     * Nettoie le polling en cours
     */
    stopScanPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            console.log('🛑 Polling arrêté');
        }
    }

    /**
     * Cache la barre de progression pour un service
     */
    hideServiceProgress(service) {
        const serviceCard = document.querySelector(`[data-service="${service}"]`);
        const progressOverlay = document.querySelector(`[data-progress-overlay="${service}"]`);
        const progressBadge = document.querySelector(`[data-progress-badge="${service}"]`);

        if (serviceCard) {
            serviceCard.classList.remove('scanning');
        }

        if (progressOverlay) {
            progressOverlay.style.width = '0%';
        }

        if (progressBadge) {
            progressBadge.textContent = '0%';
        }
    }

    /**
     * Met à jour la progression d'un service (NOUVEAU DESIGN)
     */
    updateServiceProgress(service, percentage, resourcesCount) {
        const progressOverlay = document.querySelector(`[data-progress-overlay="${service}"]`);
        const progressBadge = document.querySelector(`[data-progress-badge="${service}"]`);

        if (!progressOverlay || !progressBadge) {
            console.warn(`⚠️ Impossible de trouver les éléments de progression pour ${service}`);
            return;
        }

        // Mettre à jour l'overlay (remplissage de gauche à droite)
        progressOverlay.style.width = `${percentage}%`;

        // Mettre à jour le badge de pourcentage
        progressBadge.textContent = `${Math.round(percentage)}%`;

        console.log(`📊 ${service.toUpperCase()}: ${Math.round(percentage)}% (${resourcesCount} ressources)`);
    }

    /**
     * Marque un service comme complété (NOUVEAU DESIGN)
     */
    completeServiceProgress(service) {
        const serviceCard = document.querySelector(`[data-service="${service}"]`);
        const progressOverlay = document.querySelector(`[data-progress-overlay="${service}"]`);
        const progressBadge = document.querySelector(`[data-progress-badge="${service}"]`);

        // Mettre à jour à 100%
        if (progressOverlay) {
            progressOverlay.style.width = '100%';
        }
        if (progressBadge) {
            progressBadge.textContent = '100%';
        }

        // Retirer l'animation de scanning et ajouter la classe completed
        if (serviceCard) {
            serviceCard.classList.remove('scanning');
            serviceCard.classList.add('completed');
        }

        console.log(`✅ ${service.toUpperCase()} terminé !`);
    }

    /**
     * Marque un service en erreur (NOUVEAU DESIGN)
     */
    errorServiceProgress(service) {
        const serviceCard = document.querySelector(`[data-service="${service}"]`);
        const progressOverlay = document.querySelector(`[data-progress-overlay="${service}"]`);

        if (serviceCard) {
            serviceCard.classList.remove('scanning');
            serviceCard.classList.add('border-red-500');
        }

        if (progressOverlay) {
            progressOverlay.style.background = 'linear-gradient(90deg, rgba(239, 68, 68, 0.3) 0%, rgba(239, 68, 68, 0.15) 100%)';
        }

        console.error(`❌ ${service.toUpperCase()} en erreur`);
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
                                             'bg-slate-500/20 text-slate-400 border-slate-500/30';
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
                                scan.service_type === 's3' ? 'text-green-400' : 'text-slate-400';
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
            success: 'bg-green-500 text-white',  // ✅ Fond vert avec texte blanc
            error: 'bg-red-500 text-white',
            warning: 'bg-orange-500 text-white',
            info: 'bg-blue-500 text-white'
        };

        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 ${colors[type]} px-6 py-4 rounded-lg shadow-lg z-50 animate-fade-in`;
        notification.innerHTML = `
            <div class="flex items-center gap-3">
                <span class="material-symbols-outlined">${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}</span>
                <span class="font-medium">${message}</span>
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
                <button onclick="window.location.href='dashboard.html'"
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

