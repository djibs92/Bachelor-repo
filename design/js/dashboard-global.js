/**
 * Classe principale pour gérer le dashboard global
 */
class DashboardGlobal {
    constructor() {
        this.charts = {};
        this.autoRefreshInterval = null;
    }

    /**
     * Initialise le dashboard
     */
    async init() {
        try {
            console.log('🚀 Initialisation du dashboard global...');

            // Afficher le loader
            this.showLoader();

            // Vérifier que globalStats existe
            if (!window.globalStats) {
                throw new Error('globalStats n\'est pas défini');
            }

            // Détruire les graphiques existants
            this.destroyCharts();

            // Vérifier si un scan_id est passé en paramètre
            const urlParams = new URLSearchParams(window.location.search);
            const scanId = urlParams.get('scan_id');

            if (scanId) {
                console.log(`📊 Chargement du scan #${scanId}...`);
                await this.loadSpecificScan(scanId);
            } else {
                // Charger les données du dernier scan (comportement par défaut)
                await window.window.globalStats.loadAllData();
            }

            // Mettre à jour l'interface
            this.updateStatsCards();
            this.createCharts();
            this.updateAlertsSection();
            this.setupStatsCardListeners();

            // Masquer le loader
            this.hideLoader();

            // Démarrer le rafraîchissement automatique (toutes les 30 secondes)
            // Seulement si on affiche le dernier scan (pas un scan historique)
            if (!scanId) {
                this.startAutoRefresh();
            }

            console.log('✅ Dashboard global chargé avec succès');
        } catch (error) {
            console.error('❌ Erreur initialisation dashboard global:', error);
            this.hideLoader();
            this.showError('Erreur lors du chargement du dashboard');
        }
    }

    /**
     * Démarre le rafraîchissement automatique des données
     */
    startAutoRefresh() {
        // Arrêter l'interval existant s'il y en a un
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }

        console.log('🔄 Rafraîchissement automatique activé (toutes les 30s)');

        // Rafraîchir toutes les 30 secondes
        this.autoRefreshInterval = setInterval(async () => {
            console.log('🔄 Rafraîchissement automatique des données...');
            try {
                await this.refreshData();
            } catch (error) {
                console.error('❌ Erreur lors du rafraîchissement:', error);
            }
        }, 30000); // 30 secondes
    }

    /**
     * Arrête le rafraîchissement automatique
     */
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            console.log('⏸️ Rafraîchissement automatique désactivé');
        }
    }

    /**
     * Rafraîchit les données du dashboard sans recharger la page
     */
    async refreshData() {
        try {
            // Animation du bouton de rafraîchissement
            const refreshBtn = document.getElementById('refresh-btn');
            const refreshIcon = refreshBtn?.querySelector('.material-symbols-outlined');

            if (refreshBtn) {
                refreshBtn.disabled = true;
                refreshBtn.classList.add('opacity-50', 'cursor-not-allowed');
            }
            if (refreshIcon) {
                refreshIcon.classList.add('animate-spin');
            }

            console.log('🔄 Rafraîchissement des données...');

            // Recharger les données (dernier scan uniquement)
            await window.globalStats.loadAllData();

            // Détruire et recréer les graphiques
            this.destroyCharts();

            // Mettre à jour l'interface
            this.updateStatsCards();
            this.createCharts();
            this.updateAlertsSection();

            // Retirer l'animation
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
            if (refreshIcon) {
                refreshIcon.classList.remove('animate-spin');
            }

            console.log('✅ Données rafraîchies');

            // Afficher une notification de succès
            this.showSuccessToast('Données mises à jour');
        } catch (error) {
            console.error('❌ Erreur rafraîchissement:', error);

            // Retirer l'animation en cas d'erreur
            const refreshBtn = document.getElementById('refresh-btn');
            const refreshIcon = refreshBtn?.querySelector('.material-symbols-outlined');
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
            if (refreshIcon) {
                refreshIcon.classList.remove('animate-spin');
            }

            this.showError('Erreur lors du rafraîchissement');
        }
    }

    /**
     * Affiche un toast de succès
     */
    showSuccessToast(message) {
        const toast = document.createElement('div');
        toast.className = 'fixed bottom-4 right-4 bg-green-500/10 border border-green-500 text-green-500 px-4 py-3 rounded-lg backdrop-blur-sm z-50 animate-fade-in';
        toast.innerHTML = `
            <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-lg">check_circle</span>
                <span class="text-sm font-medium">${message}</span>
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    /**
     * Détruit tous les graphiques existants
     */
    destroyCharts() {
        Object.keys(this.charts).forEach(key => {
            if (this.charts[key] && typeof this.charts[key].destroy === 'function') {
                this.charts[key].destroy();
            }
        });
        this.charts = {};
    }

    /**
     * Charge un scan spécifique
     */
    async loadSpecificScan(scanId) {
        try {
            // Afficher un bandeau indiquant qu'on consulte un scan historique
            this.showHistoricalScanBanner(scanId);

            // Charger les données avec le scan_id spécifique
            await window.globalStats.loadAllData({ scan_id: scanId });

            console.log(`✅ Scan #${scanId} chargé`);
        } catch (error) {
            console.error(`❌ Erreur chargement scan #${scanId}:`, error);
            throw error;
        }
    }

    /**
     * Affiche un bandeau indiquant qu'on consulte un scan historique
     */
    showHistoricalScanBanner(scanId) {
        // Vérifier si le bandeau existe déjà
        let banner = document.getElementById('historical-scan-banner');

        if (!banner) {
            // Créer le bandeau
            banner = document.createElement('div');
            banner.id = 'historical-scan-banner';
            banner.className = 'fixed top-0 left-0 right-0 z-50 bg-primary/90 backdrop-blur-sm text-white px-6 py-3 flex items-center justify-between shadow-lg';
            banner.innerHTML = `
                <div class="flex items-center gap-3">
                    <span class="material-symbols-outlined">history</span>
                    <div>
                        <p class="font-semibold">Consultation d'un scan historique</p>
                        <p class="text-sm opacity-90">Scan #${scanId}</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <a href="dashbord.html" class="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors">
                        Retour au scan actuel
                    </a>
                    <button onclick="document.getElementById('historical-scan-banner').remove()" class="p-2 hover:bg-white/20 rounded-lg transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
            `;

            // Insérer au début du body
            document.body.insertBefore(banner, document.body.firstChild);

            // Ajouter un padding-top au contenu pour compenser le bandeau
            const mainContent = document.querySelector('main');
            if (mainContent) {
                mainContent.style.paddingTop = '80px';
            }
        }
    }

    /**
     * Affiche le loader
     */
    showLoader() {
        const loader = document.getElementById('dashboard-loader');
        if (loader) {
            loader.classList.remove('hidden');
        }
    }

    /**
     * Masque le loader
     */
    hideLoader() {
        const loader = document.getElementById('dashboard-loader');
        if (loader) {
            loader.classList.add('hidden');
        }
    }

    /**
     * Met à jour les stats cards
     */
    updateStatsCards() {
        // Total Resources
        const totalResources = window.globalStats.getTotalResources();
        document.getElementById('total-resources').textContent = totalResources.total;
        document.getElementById('total-resources-detail').textContent = `${totalResources.ec2} EC2 | ${totalResources.s3} S3 | ${totalResources.vpc} VPC`;

        // Active Alerts
        const alerts = window.globalStats.getActiveAlerts();
        const alertsEl = document.getElementById('active-alerts');
        alertsEl.textContent = alerts.total;
        alertsEl.className = `text-3xl font-bold mb-1 ${this.getAlertColor(alerts.total)}`;
        document.getElementById('active-alerts-detail').textContent = `${alerts.danger} critiques | ${alerts.warning} warnings`;

        // Scans This Month
        const scans = window.globalStats.getScansThisMonth();
        document.getElementById('scans-month').textContent = scans.total;
        document.getElementById('scans-month-detail').textContent = `${scans.ec2} EC2 | ${scans.s3} S3 | ${scans.vpc} VPC`;

        // Security Score
        const securityScore = window.globalStats.getSecurityScore();
        const scoreEl = document.getElementById('security-score');
        scoreEl.textContent = `${securityScore.score}%`;
        scoreEl.className = `text-3xl font-bold mb-1 ${this.getScoreColor(securityScore.score)}`;
        document.getElementById('security-score-detail').textContent = `${securityScore.passedChecks}/${securityScore.totalChecks} checks passés`;
    }

    /**
     * Retourne la couleur selon le nombre d'alertes
     */
    getAlertColor(count) {
        if (count === 0) return 'text-green-400';
        if (count <= 5) return 'text-orange-400';
        return 'text-red-400';
    }

    /**
     * Retourne la couleur selon le score de sécurité
     */
    getScoreColor(score) {
        if (score >= 80) return 'text-green-400';
        if (score >= 50) return 'text-orange-400';
        return 'text-red-400';
    }

    /**
     * Crée tous les graphiques
     */
    createCharts() {
        this.createResourceDistributionChart();
        this.createEC2RegionChart();
        this.createS3RegionChart();
        this.createVPCRegionChart();
    }

    /**
     * Graphique: Répartition des ressources (Donut moderne - style EC2)
     */
    createResourceDistributionChart() {
        const ctx = document.getElementById('chart-resource-distribution');
        if (!ctx) return;

        const data = window.globalStats.getResourceDistribution();

        this.charts.resourceDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['EC2 Instances', 'S3 Buckets', 'VPC Networks'],
                datasets: [{
                    data: [data.ec2.count, data.s3.count, data.vpc.count],
                    backgroundColor: [
                        '#3b82f6',  // Bleu EC2
                        '#10b981',  // Vert S3
                        '#fb923c'   // Orange VPC
                    ],
                    borderWidth: 0,  // Pas de bordure - clé pour la qualité !
                    hoverBorderWidth: 0,
                    hoverOffset: 15,  // Effet hover moderne
                    spacing: 3  // Espacement entre les segments
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '65%',
                layout: {
                    padding: 20  // Padding pour l'effet hover
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.98)',
                        titleColor: '#137FEC',
                        bodyColor: '#e2e8f0',
                        borderColor: '#137FEC',
                        borderWidth: 1,
                        padding: 16,
                        displayColors: true,
                        boxWidth: 12,
                        boxHeight: 12,
                        boxPadding: 6,
                        titleFont: {
                            size: 14,
                            family: 'Rajdhani',
                            weight: '600'
                        },
                        bodyFont: {
                            size: 13,
                            family: 'Rajdhani',
                            weight: '500'
                        },
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return ` ${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 1000,
                    easing: 'easeInOutQuart'
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                }
            }
        });

        // Mettre à jour les pourcentages
        const ec2PercentEl = document.getElementById('ec2-percent');
        const s3PercentEl = document.getElementById('s3-percent');
        const vpcPercentEl = document.getElementById('vpc-percent');

        if (ec2PercentEl) ec2PercentEl.textContent = `${data.ec2.percentage}%`;
        if (s3PercentEl) s3PercentEl.textContent = `${data.s3.percentage}%`;
        if (vpcPercentEl) vpcPercentEl.textContent = `${data.vpc.percentage}%`;

        // Mettre à jour le total au centre du donut
        const totalElement = document.getElementById('total-resources-donut');
        if (totalElement) {
            const total = data.ec2.count + data.s3.count + data.vpc.count;
            totalElement.textContent = total;
        }
    }

    /**
     * Graphique: Instances EC2 par région
     */
    createEC2RegionChart() {
        const data = window.globalStats.getEC2RegionDistribution();
        console.log('📊 Données EC2 par région:', data);

        if (!data.labels || data.labels.length === 0) {
            console.warn('⚠️ Aucune donnée EC2 pour le graphique régions');
            return;
        }

        const ctx = document.getElementById('chart-ec2-regions');
        if (!ctx) return;

        this.charts.ec2Regions = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Instances',
                    data: data.data,
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                    barThickness: 25  // Largeur uniforme pour toutes les barres
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#fff',
                        bodyColor: '#cbd5e1',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.x} instance${context.parsed.x > 1 ? 's' : ''}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#cbd5e1',
                            stepSize: 1,
                            font: { size: 12 }
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)',
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: '#fff',
                            font: { size: 13, weight: '500' }
                        },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Graphique: Buckets S3 par région
     */
    createS3RegionChart() {
        const data = window.globalStats.getS3RegionDistribution();
        console.log('📊 Données S3 par région:', data);

        if (!data.labels || data.labels.length === 0) {
            console.warn('⚠️ Aucune donnée S3 pour le graphique régions');
            return;
        }

        const ctx = document.getElementById('chart-s3-regions');
        if (!ctx) return;

        this.charts.s3Regions = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Buckets',
                    data: data.data,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                    barThickness: 25  // Largeur uniforme pour toutes les barres
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#fff',
                        bodyColor: '#cbd5e1',
                        borderColor: '#10b981',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.x} bucket${context.parsed.x > 1 ? 's' : ''}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#cbd5e1',
                            stepSize: 1,
                            font: { size: 12 }
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)',
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: '#fff',
                            font: { size: 13, weight: '500' }
                        },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Graphique: VPC par région (Bar chart horizontal)
     */
    createVPCRegionChart() {
        const ctx = document.getElementById('chart-vpc-regions');
        if (!ctx) return;

        const regionData = window.globalStats.getVPCRegionDistribution();

        this.charts.vpcRegions = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: regionData.labels,
                datasets: [{
                    label: 'VPCs',
                    data: regionData.data,
                    backgroundColor: 'rgba(251, 146, 60, 0.8)',  // Orange VPC
                    borderColor: 'rgba(251, 146, 60, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                    barThickness: 25  // Largeur uniforme pour toutes les barres
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#fff',
                        bodyColor: '#cbd5e1',
                        borderColor: '#fb923c',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.x} VPC${context.parsed.x > 1 ? 's' : ''}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#cbd5e1',
                            stepSize: 1,
                            font: { size: 12 }
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)',
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: '#fff',
                            font: { size: 13, weight: '500' }
                        },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Met à jour la section des alertes
     */
    updateAlertsSection() {
        const alerts = window.globalStats.getRecentCriticalAlerts();
        const container = document.getElementById('alerts-container');
        const countElement = document.getElementById('alerts-count');

        if (!container) return;

        // Mettre à jour le compteur
        if (countElement) {
            countElement.textContent = `${alerts.length} alerte${alerts.length > 1 ? 's' : ''}`;
        }

        if (alerts.length === 0) {
            container.innerHTML = `
                <div class="flex items-center justify-center py-8">
                    <div class="text-center">
                        <span class="material-symbols-outlined text-green-400 text-5xl">check_circle</span>
                        <p class="text-slate-300 mt-2">Aucune alerte critique</p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = '';

        alerts.forEach(alert => {
            const alertDiv = document.createElement('div');
            const iconColor = {
                'danger': 'text-red-400',
                'warning': 'text-orange-400',
                'info': 'text-blue-400'
            }[alert.type];

            const bgColor = {
                'danger': 'bg-red-500/20',
                'warning': 'bg-orange-500/20',
                'info': 'bg-blue-500/20'
            }[alert.type];

            const icon = {
                'danger': 'error',
                'warning': 'warning',
                'info': 'info'
            }[alert.type];

            alertDiv.className = 'flex items-start gap-3 rounded-lg bg-slate-800/40 p-3';
            alertDiv.innerHTML = `
                <div class="flex h-8 w-8 items-center justify-center rounded-full ${bgColor} ${iconColor}">
                    <span class="material-symbols-outlined text-lg">${icon}</span>
                </div>
                <div class="flex-1">
                    <p class="font-medium text-white">${alert.message}</p>
                    <p class="text-sm text-slate-400">${alert.service}: ${alert.resource}</p>
                </div>
            `;

            container.appendChild(alertDiv);
        });
    }

    /**
     * Affiche une erreur
     */
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-500/10 border border-red-500 text-red-500 px-6 py-4 rounded-lg backdrop-blur-sm z-50';
        errorDiv.innerHTML = `
            <div class="flex items-center gap-3">
                <span class="material-symbols-outlined">error</span>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    }

    /**
     * Configure les event listeners sur les stats cards
     */
    setupStatsCardListeners() {
        console.log('🔧 Configuration des event listeners...');

        // Total Resources
        const totalResourcesCard = document.querySelector('[data-modal="resources"]');
        console.log('Total Resources Card:', totalResourcesCard);
        if (totalResourcesCard) {
            totalResourcesCard.style.cursor = 'pointer';
            totalResourcesCard.addEventListener('click', () => {
                console.log('Clic sur Total Resources');
                this.showResourcesModal();
            });
        }

        // Active Alerts
        const activeAlertsCard = document.querySelector('[data-modal="alerts"]');
        console.log('Active Alerts Card:', activeAlertsCard);
        if (activeAlertsCard) {
            activeAlertsCard.style.cursor = 'pointer';
            activeAlertsCard.addEventListener('click', () => {
                console.log('Clic sur Active Alerts');
                this.showAlertsModal();
            });
        }

        // Scans This Month
        const scansCard = document.querySelector('[data-modal="scans"]');
        console.log('Scans Card:', scansCard);
        if (scansCard) {
            scansCard.style.cursor = 'pointer';
            scansCard.addEventListener('click', () => {
                console.log('Clic sur Scans');
                this.showScansModal();
            });
        }

        // Security Score
        const securityCard = document.querySelector('[data-modal="security"]');
        console.log('Security Card:', securityCard);
        if (securityCard) {
            securityCard.style.cursor = 'pointer';
            securityCard.addEventListener('click', () => {
                console.log('Clic sur Security Score');
                this.showSecurityModal();
            });
        }
    }

    /**
     * Affiche le modal des ressources
     */
    showResourcesModal() {
        const resources = window.globalStats.getAllResourcesList();
        const modal = document.getElementById('modal-resources');
        const tbody = modal.querySelector('#resources-table-body');

        tbody.innerHTML = '';

        resources.forEach(resource => {
            const row = document.createElement('tr');
            row.className = 'border-b border-slate-700 hover:bg-slate-800/50';

            // Couleur par type de ressource
            let typeColor = 'text-slate-400';
            if (resource.type === 'EC2') typeColor = 'text-blue-400';
            else if (resource.type === 'S3') typeColor = 'text-green-400';
            else if (resource.type === 'VPC') typeColor = 'text-orange-400';

            // Couleur selon l'état
            const stateColor = resource.state === 'running' || resource.state === 'active' || resource.state === 'available' ? 'text-green-400' : 'text-red-400';

            row.innerHTML = `
                <td class="px-4 py-3"><span class="font-medium ${typeColor}">${resource.type}</span></td>
                <td class="px-4 py-3 text-white">${resource.name}</td>
                <td class="px-4 py-3 text-slate-300 font-mono text-sm">${resource.id}</td>
                <td class="px-4 py-3 text-slate-300">${resource.region}</td>
                <td class="px-4 py-3"><span class="${stateColor}">${resource.state}</span></td>
                <td class="px-4 py-3 text-slate-300">${resource.instanceType}</td>
            `;
            tbody.appendChild(row);
        });

        this.openModal('modal-resources');
    }

    /**
     * Affiche le modal des alertes
     */
    showAlertsModal() {
        const alertsData = window.globalStats.getActiveAlerts();
        const modal = document.getElementById('modal-alerts');
        const container = modal.querySelector('#alerts-list');

        container.innerHTML = '';

        if (alertsData.total === 0) {
            container.innerHTML = `
                <div class="flex items-center justify-center py-8">
                    <div class="text-center">
                        <span class="material-symbols-outlined text-green-400 text-5xl">check_circle</span>
                        <p class="text-slate-300 mt-2">Aucune alerte</p>
                    </div>
                </div>
            `;
        } else {
            // Grouper par type
            const grouped = {
                danger: alertsData.alerts.filter(a => a.type === 'danger'),
                warning: alertsData.alerts.filter(a => a.type === 'warning'),
                info: alertsData.alerts.filter(a => a.type === 'info')
            };

            // Afficher les critiques
            if (grouped.danger.length > 0) {
                container.innerHTML += `<h3 class="text-red-400 font-semibold mb-2 flex items-center gap-2">
                    <span class="material-symbols-outlined">error</span> Critiques (${grouped.danger.length})
                </h3>`;
                grouped.danger.forEach(alert => {
                    container.innerHTML += this.createAlertItem(alert, 'danger');
                });
            }

            // Afficher les warnings
            if (grouped.warning.length > 0) {
                container.innerHTML += `<h3 class="text-orange-400 font-semibold mb-2 mt-4 flex items-center gap-2">
                    <span class="material-symbols-outlined">warning</span> Warnings (${grouped.warning.length})
                </h3>`;
                grouped.warning.forEach(alert => {
                    container.innerHTML += this.createAlertItem(alert, 'warning');
                });
            }

            // Afficher les infos
            if (grouped.info.length > 0) {
                container.innerHTML += `<h3 class="text-blue-400 font-semibold mb-2 mt-4 flex items-center gap-2">
                    <span class="material-symbols-outlined">info</span> Informations (${grouped.info.length})
                </h3>`;
                grouped.info.forEach(alert => {
                    container.innerHTML += this.createAlertItem(alert, 'info');
                });
            }
        }

        this.openModal('modal-alerts');
    }

    /**
     * Crée un élément d'alerte
     */
    createAlertItem(alert, type) {
        const colors = {
            danger: { bg: 'bg-red-500/20', text: 'text-red-400', icon: 'error' },
            warning: { bg: 'bg-orange-500/20', text: 'text-orange-400', icon: 'warning' },
            info: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: 'info' }
        };

        const color = colors[type];

        return `
            <div class="flex items-start gap-3 rounded-lg bg-slate-800/40 p-3 mb-2">
                <div class="flex h-8 w-8 items-center justify-center rounded-full ${color.bg} ${color.text}">
                    <span class="material-symbols-outlined text-lg">${color.icon}</span>
                </div>
                <div class="flex-1">
                    <p class="font-medium text-white">${alert.message}</p>
                    <p class="text-sm text-slate-400">${alert.service}: ${alert.resource}</p>
                </div>
            </div>
        `;
    }

    /**
     * Affiche le modal des scans - Groupés par scan_run_id
     */
    showScansModal() {
        const scansData = window.globalStats.getScansThisMonth();
        const modal = document.getElementById('modal-scans');
        const tbody = modal.querySelector('#scans-table-body');

        tbody.innerHTML = '';

        // Grouper les scans par timestamp (même scan = même timestamp proche)
        const groupedScans = this.groupScansByTimestamp(scansData.scans);

        groupedScans.forEach(scanGroup => {
            const row = document.createElement('tr');
            row.className = 'border-b border-slate-700 hover:bg-slate-800/50 cursor-pointer transition-colors';
            row.dataset.scanGroup = JSON.stringify(scanGroup.scans);

            const date = new Date(scanGroup.timestamp);
            const formattedDate = date.toLocaleDateString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            // Créer la liste des services scannés
            const services = scanGroup.scans.map(s => s.service_type.toUpperCase()).join(', ');
            const totalResources = scanGroup.scans.reduce((sum, s) => sum + (s.total_resources || 0), 0);

            // Déterminer le statut global
            const hasSuccess = scanGroup.scans.some(s => s.status === 'success');
            const hasFailed = scanGroup.scans.some(s => s.status === 'failed');
            const statusColor = hasFailed ? 'text-red-400' : hasSuccess ? 'text-green-400' : 'text-orange-400';
            const statusText = hasFailed ? 'Partiel' : hasSuccess ? 'Complété' : 'En cours';

            row.innerHTML = `
                <td class="px-4 py-3 text-slate-300 font-mono text-sm">#${scanGroup.id}</td>
                <td class="px-4 py-3 text-slate-300">${formattedDate}</td>
                <td class="px-4 py-3">
                    <div class="flex gap-2 flex-wrap">
                        ${scanGroup.scans.map(s => {
                            const color = s.service_type === 'ec2' ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' :
                                         s.service_type === 's3' ? 'bg-green-500/20 text-green-400 border-green-500/30' :
                                         'bg-purple-500/20 text-purple-400 border-purple-500/30';
                            return `<span class="px-2 py-1 rounded-md text-xs font-medium border ${color}">${s.service_type.toUpperCase()}</span>`;
                        }).join('')}
                    </div>
                </td>
                <td class="px-4 py-3"><span class="${statusColor} font-medium">${statusText}</span></td>
                <td class="px-4 py-3 text-slate-300 font-semibold">${totalResources}</td>
            `;

            // Ajouter l'événement de clic pour afficher les détails
            row.addEventListener('click', () => this.showScanDetailsModal(scanGroup));

            tbody.appendChild(row);
        });

        this.openModal('modal-scans');
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
                    id: scan.scan_id || scan.id,  // ✅ L'API retourne "scan_id"
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
     * Affiche le modal de détails d'un scan
     */
    showScanDetailsModal(scanGroup) {
        const modal = document.getElementById('modal-scan-details');
        if (!modal) {
            console.error('❌ Modal scan-details non trouvé');
            return;
        }

        // Mettre à jour le titre
        const date = new Date(scanGroup.timestamp);
        const formattedDate = date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        document.getElementById('scan-details-title').textContent = `Scan #${scanGroup.id} - ${formattedDate}`;

        // Remplir le contenu
        const container = document.getElementById('scan-details-content');
        container.innerHTML = '';

        scanGroup.scans.forEach(scan => {
            const serviceColor = scan.service_type === 'ec2' ? 'blue' :
                                scan.service_type === 's3' ? 'green' : 'purple';

            const statusColor = scan.status === 'success' ? 'green' :
                               scan.status === 'failed' ? 'red' : 'orange';

            const serviceCard = document.createElement('div');
            serviceCard.className = 'glass-card p-4 border border-slate-700';
            serviceCard.innerHTML = `
                <div class="flex items-center justify-between mb-3">
                    <h4 class="text-lg font-semibold text-${serviceColor}-400 flex items-center gap-2">
                        <span class="material-symbols-outlined">cloud</span>
                        ${scan.service_type.toUpperCase()}
                    </h4>
                    <span class="px-3 py-1 rounded-full text-xs font-medium bg-${statusColor}-500/20 text-${statusColor}-400 border border-${statusColor}-500/30">
                        ${scan.status}
                    </span>
                </div>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p class="text-slate-400">Ressources trouvées</p>
                        <p class="text-white font-semibold text-xl">${scan.total_resources || 0}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Client ID</p>
                        <p class="text-white font-mono text-xs">${scan.client_id || 'N/A'}</p>
                    </div>
                </div>
            `;
            container.appendChild(serviceCard);
        });

        this.openModal('modal-scan-details');
    }

    /**
     * Affiche le modal du score de sécurité
     */
    showSecurityModal() {
        const securityData = window.globalStats.getSecurityScore();
        const alertsData = window.globalStats.getActiveAlerts();
        const modal = document.getElementById('modal-security');
        const container = modal.querySelector('#security-checks');

        container.innerHTML = '';

        // Afficher le score global
        const scoreColor = securityData.score >= 80 ? 'text-green-400' :
                          securityData.score >= 50 ? 'text-orange-400' : 'text-red-400';

        container.innerHTML = `
            <div class="text-center mb-6">
                <p class="text-6xl font-bold ${scoreColor}">${securityData.score}%</p>
                <p class="text-slate-300 mt-2">${securityData.passedChecks} / ${securityData.totalChecks} checks passés</p>
            </div>
        `;

        // Checks passés
        container.innerHTML += `
            <h3 class="text-green-400 font-semibold mb-2 flex items-center gap-2">
                <span class="material-symbols-outlined">check_circle</span> Checks Passés (${securityData.passedChecks})
            </h3>
        `;

        // Analyser les checks EC2
        window.globalStats.ec2Instances.forEach(instance => {
            if (instance.public_ip) {
                container.innerHTML += this.createCheckItem(
                    `EC2: ${instance.name || instance.instance_id}`,
                    'IP publique configurée',
                    true
                );
            }
            if (instance.tags && Object.keys(instance.tags).length > 0) {
                container.innerHTML += this.createCheckItem(
                    `EC2: ${instance.name || instance.instance_id}`,
                    'Tags configurés',
                    true
                );
            }
        });

        // Analyser les checks S3
        window.globalStats.s3Buckets.forEach(bucket => {
            if (bucket.encryption_enabled) {
                container.innerHTML += this.createCheckItem(
                    `S3: ${bucket.bucket_name}`,
                    'Encryption activé',
                    true
                );
            }
            if (bucket.public_access_blocked && !bucket.public_read_enabled) {
                container.innerHTML += this.createCheckItem(
                    `S3: ${bucket.bucket_name}`,
                    'Public Access bloqué',
                    true
                );
            }
            if (bucket.versioning_enabled) {
                container.innerHTML += this.createCheckItem(
                    `S3: ${bucket.bucket_name}`,
                    'Versioning activé',
                    true
                );
            }
            if (bucket.logging_enabled) {
                container.innerHTML += this.createCheckItem(
                    `S3: ${bucket.bucket_name}`,
                    'Logging activé',
                    true
                );
            }
        });

        // Analyser les checks VPC
        window.globalStats.vpcInstances.forEach(vpc => {
            const vpcName = vpc.tags?.Name || vpc.vpc_id;
            if (vpc.flow_logs_enabled) {
                container.innerHTML += this.createCheckItem(
                    `VPC: ${vpcName}`,
                    'Flow Logs activé',
                    true
                );
            }
            if (vpc.internet_gateway_attached) {
                container.innerHTML += this.createCheckItem(
                    `VPC: ${vpcName}`,
                    'Internet Gateway attaché',
                    true
                );
            }
            if (vpc.tags && (typeof vpc.tags === 'object' ? Object.keys(vpc.tags).length > 0 : vpc.tags.length > 0)) {
                container.innerHTML += this.createCheckItem(
                    `VPC: ${vpcName}`,
                    'Tags configurés',
                    true
                );
            }
        });

        // Checks échoués
        if (securityData.failedChecks > 0) {
            container.innerHTML += `
                <h3 class="text-red-400 font-semibold mb-2 mt-4 flex items-center gap-2">
                    <span class="material-symbols-outlined">cancel</span> Checks Échoués (${securityData.failedChecks})
                </h3>
            `;

            // Analyser les checks EC2 échoués
            window.globalStats.ec2Instances.forEach(instance => {
                if (!instance.public_ip) {
                    container.innerHTML += this.createCheckItem(
                        `EC2: ${instance.name || instance.instance_id}`,
                        'Pas d\'IP publique',
                        false
                    );
                }
                if (!instance.tags || Object.keys(instance.tags).length === 0) {
                    container.innerHTML += this.createCheckItem(
                        `EC2: ${instance.name || instance.instance_id}`,
                        'Pas de tags',
                        false
                    );
                }
            });

            // Analyser les checks S3 échoués
            window.globalStats.s3Buckets.forEach(bucket => {
                if (!bucket.encryption_enabled) {
                    container.innerHTML += this.createCheckItem(
                        `S3: ${bucket.bucket_name}`,
                        'Encryption désactivé',
                        false
                    );
                }
                if (!bucket.public_access_blocked || bucket.public_read_enabled) {
                    container.innerHTML += this.createCheckItem(
                        `S3: ${bucket.bucket_name}`,
                        'Public Access non bloqué',
                        false
                    );
                }
                if (!bucket.versioning_enabled) {
                    container.innerHTML += this.createCheckItem(
                        `S3: ${bucket.bucket_name}`,
                        'Versioning désactivé',
                        false
                    );
                }
                if (!bucket.logging_enabled) {
                    container.innerHTML += this.createCheckItem(
                        `S3: ${bucket.bucket_name}`,
                        'Logging désactivé',
                        false
                    );
                }
            });

            // Analyser les checks VPC échoués
            window.globalStats.vpcInstances.forEach(vpc => {
                const vpcName = vpc.tags?.Name || vpc.vpc_id;
                if (!vpc.flow_logs_enabled) {
                    container.innerHTML += this.createCheckItem(
                        `VPC: ${vpcName}`,
                        'Flow Logs désactivé',
                        false
                    );
                }
                if (!vpc.internet_gateway_attached) {
                    container.innerHTML += this.createCheckItem(
                        `VPC: ${vpcName}`,
                        'Pas d\'Internet Gateway',
                        false
                    );
                }
                if (!vpc.tags || (typeof vpc.tags === 'object' ? Object.keys(vpc.tags).length === 0 : vpc.tags.length === 0)) {
                    container.innerHTML += this.createCheckItem(
                        `VPC: ${vpcName}`,
                        'Pas de tags',
                        false
                    );
                }
            });
        }

        this.openModal('modal-security');
    }

    /**
     * Crée un élément de check
     */
    createCheckItem(resource, message, passed) {
        const color = passed ? 'text-green-400' : 'text-red-400';
        const icon = passed ? 'check_circle' : 'cancel';
        const bg = passed ? 'bg-green-500/10' : 'bg-red-500/10';

        return `
            <div class="flex items-center gap-3 rounded-lg ${bg} p-2 mb-1">
                <span class="material-symbols-outlined ${color} text-lg">${icon}</span>
                <div class="flex-1">
                    <p class="text-sm text-white">${resource}</p>
                    <p class="text-xs text-slate-400">${message}</p>
                </div>
            </div>
        `;
    }

    /**
     * Ouvre un modal
     */
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    /**
     * Ferme un modal
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }
}
