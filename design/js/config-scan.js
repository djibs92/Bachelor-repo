/**
 * Classe pour gérer la configuration et le lancement des scans
 */
class ConfigScan {
    constructor() {
        this.selectedServices = ['ec2', 's3']; // Services sélectionnés par défaut
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

        const isActive = card.classList.contains('active');
        
        if (isActive) {
            // Désactiver
            card.classList.remove('active');
            checkbox.checked = false;
            this.selectedServices = this.selectedServices.filter(s => s !== service);
        } else {
            // Activer
            card.classList.add('active');
            checkbox.checked = true;
            this.selectedServices.push(service);
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

        console.log('🚀 Lancement du scan...');
        console.log('Services:', this.selectedServices);
        console.log('Régions:', this.selectedRegions);

        try {
            // Afficher le statut
            this.showScanStatus();

            // Lancer les scans pour chaque service
            for (const service of this.selectedServices) {
                await this.scanService(service);
            }

            this.showNotification('Scan terminé avec succès !', 'success');
            this.hideScanStatus();
            
            // Recharger l'historique
            await this.loadScanHistory();

        } catch (error) {
            console.error('❌ Erreur lors du scan:', error);
            this.showNotification('Erreur lors du scan: ' + error.message, 'error');
            this.hideScanStatus();
        }
    }

    /**
     * Scanne un service spécifique
     */
    async scanService(service) {
        console.log(`📡 Scan ${service.toUpperCase()}...`);
        
        // Mettre à jour le statut
        document.getElementById('current-service').textContent = service.toUpperCase();
        document.getElementById('current-region').textContent = this.selectedRegions.join(', ');

        // Préparer la requête
        const scanRequest = {
            provider: 'aws',
            services: [service],
            auth_mode: {
                type: 'sts',
                role_arn: 'arn:aws:iam::730335226954:role/CloudDiagnoze-ScanRole' // Role ARN réel
            },
            client_id: 'ASM-Enterprise', // TODO: À récupérer de l'authentification
            regions: this.selectedRegions
        };

        try {
            // Appeler l'API avec le token JWT
            const response = await fetch(`${API_CONFIG.BASE_URL}/scans`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authManager.getToken()}`  // ✅ AJOUT DU TOKEN JWT
                },
                body: JSON.stringify(scanRequest)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log(`✅ Scan ${service} lancé:`, data);

            // Simuler la progression (en attendant le vrai statut)
            await this.simulateScanProgress(service);

        } catch (error) {
            console.error(`❌ Erreur scan ${service}:`, error);
            throw error;
        }
    }

    /**
     * Simule la progression du scan (temporaire)
     */
    async simulateScanProgress(service) {
        return new Promise((resolve) => {
            let resources = 0;
            const interval = setInterval(() => {
                resources += Math.floor(Math.random() * 3) + 1;
                document.getElementById('resources-found').textContent = resources;
            }, 500);

            setTimeout(() => {
                clearInterval(interval);
                resolve();
            }, 3000);
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
            const data = await api.getScansHistory({ limit: 10 });
            this.renderScanHistory(data.scans || []);
        } catch (error) {
            console.error('❌ Erreur chargement historique:', error);
        }
    }

    /**
     * Affiche l'historique des scans
     */
    renderScanHistory(scans) {
        const container = document.getElementById('scan-history');
        if (!container) return;

        if (scans.length === 0) {
            container.innerHTML = '<p class="text-slate-400 text-sm text-center py-4">Aucun scan pour le moment</p>';
            return;
        }

        container.innerHTML = '';

        scans.slice(0, 5).forEach(scan => {
            const date = new Date(scan.scan_timestamp);
            const formattedDate = date.toLocaleDateString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });

            const statusColor = scan.status === 'success' ? 'text-green-400' : 
                              scan.status === 'partial' ? 'text-orange-400' : 'text-red-400';
            
            const serviceColor = scan.service_type === 'ec2' ? 'text-blue-400' : 'text-green-400';

            const div = document.createElement('div');
            div.className = 'glass-card rounded-lg p-3 border border-slate-700';
            div.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <span class="font-semibold ${serviceColor}">${scan.service_type.toUpperCase()}</span>
                    <span class="text-xs ${statusColor}">${scan.status}</span>
                </div>
                <div class="flex items-center justify-between text-xs text-slate-400">
                    <span>${formattedDate}</span>
                    <span>${scan.total_resources || 0} ressources</span>
                </div>
            `;
            container.appendChild(div);
        });
    }

    /**
     * Réinitialise la configuration
     */
    resetConfig() {
        // Réinitialiser les services
        this.selectedServices = ['ec2', 's3'];
        document.querySelectorAll('.service-card').forEach(card => {
            const service = card.getAttribute('data-service');
            const checkbox = card.querySelector('input[type="checkbox"]');
            
            if (service === 'ec2' || service === 's3') {
                card.classList.add('active');
                if (checkbox) checkbox.checked = true;
            } else {
                card.classList.remove('active');
                if (checkbox) checkbox.checked = false;
            }
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
}

