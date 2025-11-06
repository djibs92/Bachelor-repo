/**
 * Classe principale pour gérer le dashboard global
 */
class DashboardGlobal {
    constructor() {
        this.charts = {};
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

            // Charger les données
            await window.window.globalStats.loadAllData();

            // Mettre à jour l'interface
            this.updateStatsCards();
            this.createCharts();
            this.updateAlertsSection();
            this.setupStatsCardListeners();

            // Masquer le loader
            this.hideLoader();

            console.log('✅ Dashboard global chargé avec succès');
        } catch (error) {
            console.error('❌ Erreur initialisation dashboard global:', error);
            this.hideLoader();
            this.showError('Erreur lors du chargement du dashboard');
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
        document.getElementById('total-resources-detail').textContent = `${totalResources.ec2} EC2 | ${totalResources.s3} S3`;

        // Active Alerts
        const alerts = window.globalStats.getActiveAlerts();
        const alertsEl = document.getElementById('active-alerts');
        alertsEl.textContent = alerts.total;
        alertsEl.className = `text-3xl font-bold mb-1 ${this.getAlertColor(alerts.total)}`;
        document.getElementById('active-alerts-detail').textContent = `${alerts.danger} critiques | ${alerts.warning} warnings`;

        // Scans This Month
        const scans = window.globalStats.getScansThisMonth();
        document.getElementById('scans-month').textContent = scans.total;
        document.getElementById('scans-month-detail').textContent = `${scans.ec2} EC2 | ${scans.s3} S3`;

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
    }

    /**
     * Graphique: Répartition des ressources (Donut)
     */
    createResourceDistributionChart() {
        const ctx = document.getElementById('chart-resource-distribution');
        if (!ctx) return;

        const data = window.globalStats.getResourceDistribution();

        this.charts.resourceDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['EC2 Instances', 'S3 Buckets'],
                datasets: [{
                    data: [data.ec2.count, data.s3.count],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)'
                    ],
                    borderColor: 'rgba(15, 23, 42, 0.8)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: { color: '#cbd5e1', font: { size: 12 } }
                    }
                }
            }
        });

        // Mettre à jour les pourcentages
        const ec2PercentEl = document.getElementById('ec2-percent');
        const s3PercentEl = document.getElementById('s3-percent');

        if (ec2PercentEl) ec2PercentEl.textContent = `${data.ec2.percentage}%`;
        if (s3PercentEl) s3PercentEl.textContent = `${data.s3.percentage}%`;
    }

    /**
     * Graphique: Instances EC2 par région (Bar)
     */
    createEC2RegionChart() {
        const ctx = document.getElementById('chart-ec2-regions');
        if (!ctx) {
            console.error('❌ Canvas chart-ec2-regions non trouvé');
            return;
        }

        const data = window.globalStats.getEC2RegionDistribution();
        console.log('📊 Données EC2 par région:', data);

        if (!data.labels || data.labels.length === 0) {
            console.warn('⚠️ Aucune donnée EC2 pour le graphique régions');
            return;
        }

        this.charts.ec2Regions = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Instances',
                    data: data.data,
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#cbd5e1',
                            stepSize: 1
                        },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                    },
                    x: {
                        ticks: { color: '#cbd5e1' },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    /**
     * Graphique: Régions S3 (Bar Horizontal)
     */
    createS3RegionChart() {
        const ctx = document.getElementById('chart-s3-regions');
        if (!ctx) {
            console.error('❌ Canvas chart-s3-regions non trouvé');
            return;
        }

        const data = window.globalStats.getS3RegionDistribution();
        console.log('📊 Données S3 par région:', data);

        if (!data.labels || data.labels.length === 0) {
            console.warn('⚠️ Aucune donnée S3 pour le graphique régions');
            return;
        }

        this.charts.s3Regions = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Buckets',
                    data: data.data,
                    backgroundColor: 'rgba(168, 85, 247, 0.8)',
                    borderColor: 'rgba(168, 85, 247, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#cbd5e1',
                            stepSize: 1
                        },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#cbd5e1' },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
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
        
        if (!container) return;

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

            const typeColor = resource.type === 'EC2' ? 'text-blue-400' : 'text-green-400';
            const stateColor = resource.state === 'running' || resource.state === 'active' ? 'text-green-400' : 'text-red-400';

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
     * Affiche le modal des scans
     */
    showScansModal() {
        const scansData = window.globalStats.getScansThisMonth();
        const modal = document.getElementById('modal-scans');
        const tbody = modal.querySelector('#scans-table-body');

        tbody.innerHTML = '';

        scansData.scans.forEach(scan => {
            const row = document.createElement('tr');
            row.className = 'border-b border-slate-700 hover:bg-slate-800/50';

            const date = new Date(scan.scan_timestamp);
            const formattedDate = date.toLocaleDateString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            const serviceColor = scan.service_type === 'ec2' ? 'text-blue-400' : 'text-green-400';
            const statusColor = scan.status === 'completed' ? 'text-green-400' : 'text-orange-400';

            row.innerHTML = `
                <td class="px-4 py-3 text-slate-300">${formattedDate}</td>
                <td class="px-4 py-3"><span class="font-medium ${serviceColor}">${scan.service_type.toUpperCase()}</span></td>
                <td class="px-4 py-3"><span class="${statusColor}">${scan.status}</span></td>
                <td class="px-4 py-3 text-slate-300">${scan.resources_found || 0}</td>
            `;
            tbody.appendChild(row);
        });

        this.openModal('modal-scans');
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
