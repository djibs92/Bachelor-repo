/**
 * Classe principale pour gérer le dashboard S3
 */
class DashboardS3 {
    constructor() {
        this.charts = {};
        this.filteredBuckets = [];
    }

    /**
     * Initialise le dashboard
     */
    async init() {
        try {
            console.log('🚀 Initialisation du dashboard S3...');
            
            // Charger les données
            await s3Stats.loadBuckets();
            this.filteredBuckets = s3Stats.buckets;

            // Mettre à jour l'interface
            this.updateStatsCards();
            this.createCharts();
            this.updateAlertsSection();
            this.updateBucketsTable();
            this.setupEventListeners();
            this.populateRegionFilter();

            console.log('✅ Dashboard S3 chargé avec succès');
        } catch (error) {
            console.error('❌ Erreur initialisation dashboard S3:', error);
            this.showError('Erreur lors du chargement du dashboard');
        }
    }

    /**
     * Met à jour les stats cards
     */
    updateStatsCards() {
        // Total Buckets
        const totalStats = s3Stats.getTotalBucketsStats();
        document.getElementById('total-buckets').textContent = totalStats.total;
        document.getElementById('buckets-regions').textContent = `${totalStats.totalRegions} région(s)`;

        // Encryption
        const encryptionStats = s3Stats.getEncryptionStats();
        const encryptionEl = document.getElementById('encryption-percentage');
        encryptionEl.textContent = `${encryptionStats.percentage}%`;
        encryptionEl.className = `text-3xl font-bold mb-1 ${this.getSecurityColor(encryptionStats.percentage)}`;
        document.getElementById('encryption-detail').textContent = `${encryptionStats.encrypted}/${encryptionStats.total} chiffrés`;

        // Public Access
        const publicAccessStats = s3Stats.getPublicAccessStats();
        const publicAccessEl = document.getElementById('public-access-percentage');
        publicAccessEl.textContent = `${publicAccessStats.percentage}%`;
        publicAccessEl.className = `text-3xl font-bold mb-1 ${this.getSecurityColor(publicAccessStats.percentage)}`;
        document.getElementById('public-access-detail').textContent = `${publicAccessStats.blocked}/${publicAccessStats.total} protégés`;

        // Versioning
        const versioningStats = s3Stats.getVersioningStats();
        const versioningEl = document.getElementById('versioning-percentage');
        versioningEl.textContent = `${versioningStats.percentage}%`;
        versioningEl.className = `text-3xl font-bold mb-1 ${this.getVersioningColor(versioningStats.percentage)}`;
        document.getElementById('versioning-detail').textContent = `${versioningStats.enabled}/${versioningStats.total} activé`;

        // Requests
        const requestsStats = s3Stats.getRequestsStats();
        document.getElementById('total-requests').textContent = requestsStats.total.toLocaleString();
        document.getElementById('requests-detail').textContent = `GET: ${requestsStats.get} | PUT: ${requestsStats.put}`;

        // Data Transfer
        const transferStats = s3Stats.getDataTransferStats();
        document.getElementById('total-transfer').textContent = transferStats.totalFormatted;
        document.getElementById('transfer-detail').textContent = `↓ ${transferStats.downloadFormatted} | ↑ ${transferStats.uploadFormatted}`;
    }

    /**
     * Retourne la couleur selon le pourcentage de sécurité
     */
    getSecurityColor(percentage) {
        if (percentage === 100) return 'text-green-400';
        if (percentage >= 50) return 'text-orange-400';
        return 'text-red-400';
    }

    /**
     * Retourne la couleur pour le versioning
     */
    getVersioningColor(percentage) {
        if (percentage >= 50) return 'text-green-400';
        if (percentage > 0) return 'text-orange-400';
        return 'text-slate-400';
    }

    /**
     * Crée tous les graphiques
     */
    createCharts() {
        this.createRegionsChart();
        this.createSecurityChart();
        this.createFeaturesChart();
        this.createActivityChart();
    }

    /**
     * Graphique: Répartition par Région (Donut)
     */
    createRegionsChart() {
        const ctx = document.getElementById('chart-regions');
        const data = s3Stats.getRegionDistribution();

        this.charts.regions = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.data,
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(168, 85, 247, 0.8)'
                    ],
                    borderColor: 'rgba(15, 23, 42, 0.8)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        display: true,
                        position: 'right',
                        labels: {
                            color: '#cbd5e1',
                            font: { size: 11 },
                            padding: 10,
                            boxWidth: 12
                        }
                    }
                }
            }
        });
    }

    /**
     * Graphique: État de Sécurité (Stacked Bar)
     */
    createSecurityChart() {
        const ctx = document.getElementById('chart-security');
        const data = s3Stats.getSecurityStateDistribution();

        this.charts.security = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Activé',
                        data: data.enabled,
                        backgroundColor: 'rgba(16, 185, 129, 0.8)',
                        borderColor: 'rgba(16, 185, 129, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Désactivé',
                        data: data.disabled,
                        backgroundColor: 'rgba(239, 68, 68, 0.8)',
                        borderColor: 'rgba(239, 68, 68, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: {
                        stacked: true,
                        ticks: { color: '#cbd5e1' },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                    },
                    y: {
                        stacked: true,
                        ticks: { color: '#cbd5e1' },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: { color: '#cbd5e1', font: { size: 12 } }
                    }
                }
            }
        });
    }

    /**
     * Graphique: Fonctionnalités Avancées (Bar)
     */
    createFeaturesChart() {
        const ctx = document.getElementById('chart-features');
        const data = s3Stats.getAdvancedFeaturesDistribution();

        this.charts.features = new Chart(ctx, {
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
     * Graphique: Activité par Bucket (Stacked Bar)
     */
    createActivityChart() {
        const ctx = document.getElementById('chart-activity');
        const data = s3Stats.getActivityByBucket();

        if (!data.hasActivity) {
            ctx.style.display = 'none';
            document.getElementById('no-activity').classList.remove('hidden');
            return;
        }

        this.charts.activity = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'GET',
                        data: data.get,
                        backgroundColor: 'rgba(59, 130, 246, 0.8)',
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'PUT',
                        data: data.put,
                        backgroundColor: 'rgba(16, 185, 129, 0.8)',
                        borderColor: 'rgba(16, 185, 129, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'DELETE',
                        data: data.delete,
                        backgroundColor: 'rgba(239, 68, 68, 0.8)',
                        borderColor: 'rgba(239, 68, 68, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: {
                        stacked: true,
                        ticks: { color: '#cbd5e1' },
                        grid: { display: false }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        ticks: { color: '#cbd5e1' },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: { color: '#cbd5e1', font: { size: 12 } }
                    }
                }
            }
        });
    }

    /**
     * Met à jour la section des alertes
     */
    updateAlertsSection() {
        const alerts = s3Stats.getAlerts();
        const section = document.getElementById('alerts-section');
        const container = document.getElementById('alerts-container');

        if (alerts.length === 0) {
            section.classList.add('hidden');
            return;
        }

        section.classList.remove('hidden');
        container.innerHTML = '';

        alerts.forEach(alert => {
            const alertDiv = document.createElement('div');
            const bgColor = {
                'danger': 'bg-red-500/10 border-red-500',
                'warning': 'bg-orange-500/10 border-orange-500',
                'success': 'bg-green-500/10 border-green-500',
                'info': 'bg-blue-500/10 border-blue-500'
            }[alert.type];

            const iconColor = {
                'danger': 'text-red-500',
                'warning': 'text-orange-500',
                'success': 'text-green-500',
                'info': 'text-blue-500'
            }[alert.type];

            alertDiv.className = `${bgColor} border rounded-lg p-4`;
            alertDiv.innerHTML = `
                <div class="flex items-start gap-3">
                    <span class="material-symbols-outlined ${iconColor}">${alert.icon}</span>
                    <div class="flex-1">
                        <h4 class="font-semibold text-white mb-1">${alert.title}</h4>
                        <p class="text-sm text-slate-300">${alert.message}</p>
                    </div>
                </div>
            `;

            container.appendChild(alertDiv);
        });
    }

    /**
     * Peuple le filtre de régions
     */
    populateRegionFilter() {
        const regionFilter = document.getElementById('filter-region');
        const regions = s3Stats.getTotalBucketsStats().regions;

        regions.forEach(region => {
            const option = document.createElement('option');
            option.value = region;
            option.textContent = region;
            regionFilter.appendChild(option);
        });
    }

    /**
     * Affiche le tableau des buckets
     */
    updateBucketsTable() {
        const tbody = document.getElementById('buckets-table-body');
        const noBuckets = document.getElementById('no-buckets');

        if (this.filteredBuckets.length === 0) {
            tbody.innerHTML = '';
            noBuckets.classList.remove('hidden');
            return;
        }

        noBuckets.classList.add('hidden');
        tbody.innerHTML = '';

        this.filteredBuckets.forEach(bucket => {
            const row = document.createElement('tr');
            row.className = 'border-b border-slate-800 hover:bg-slate-800/30 cursor-pointer';
            row.dataset.bucketName = bucket.bucket_name;

            const encryptionBadge = this.getBooleanBadge(bucket.encryption_enabled);
            const versioningBadge = this.getBooleanBadge(bucket.versioning_enabled);
            const publicAccessBadge = bucket.public_access_blocked
                ? '<span class="px-2 py-1 rounded text-xs bg-green-500/20 text-green-400">Bloqué</span>'
                : '<span class="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400">Ouvert</span>';

            const requests = bucket.performance?.all_requests || 0;
            const transfer = (bucket.performance?.bytes_downloaded || 0) + (bucket.performance?.bytes_uploaded || 0);
            const transferFormatted = s3Stats.formatBytes(transfer);

            const creationDate = bucket.creation_date
                ? new Date(bucket.creation_date).toLocaleDateString('fr-FR', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric'
                })
                : '-';

            row.innerHTML = `
                <td class="py-3 font-medium">${bucket.bucket_name}</td>
                <td class="py-3">${bucket.region}</td>
                <td class="py-3">${encryptionBadge}</td>
                <td class="py-3">${versioningBadge}</td>
                <td class="py-3">${publicAccessBadge}</td>
                <td class="py-3">${requests > 0 ? requests.toLocaleString() : '-'}</td>
                <td class="py-3">${transfer > 0 ? transferFormatted : '-'}</td>
                <td class="py-3 text-xs">${creationDate}</td>
            `;

            // Event listener pour ouvrir le modal
            row.addEventListener('click', () => this.openBucketModal(bucket));

            tbody.appendChild(row);
        });

        console.log(`✅ ${this.filteredBuckets.length} buckets affichés dans le tableau`);
    }

    /**
     * Retourne un badge pour un booléen
     */
    getBooleanBadge(value) {
        if (value) {
            return '<span class="px-2 py-1 rounded text-xs bg-green-500/20 text-green-400">✓</span>';
        } else {
            return '<span class="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400">✗</span>';
        }
    }

    /**
     * Filtre par région
     */
    filterByRegion(region) {
        if (region === 'all') {
            this.filteredBuckets = s3Stats.buckets;
        } else {
            this.filteredBuckets = s3Stats.buckets.filter(b => b.region === region);
        }
        this.applySecurityFilter();
    }

    /**
     * Filtre par sécurité
     */
    filterBySecurity(security) {
        const regionFilter = document.getElementById('filter-region').value;

        // Appliquer d'abord le filtre de région
        if (regionFilter === 'all') {
            this.filteredBuckets = s3Stats.buckets;
        } else {
            this.filteredBuckets = s3Stats.buckets.filter(b => b.region === regionFilter);
        }

        // Puis appliquer le filtre de sécurité
        if (security !== 'all') {
            this.filteredBuckets = this.filteredBuckets.filter(bucket => {
                switch (security) {
                    case 'encrypted':
                        return bucket.encryption_enabled;
                    case 'not-encrypted':
                        return !bucket.encryption_enabled;
                    case 'public':
                        return !bucket.public_access_blocked || bucket.public_read_enabled;
                    case 'protected':
                        return bucket.public_access_blocked && !bucket.public_read_enabled;
                    default:
                        return true;
                }
            });
        }

        this.applySearchFilter();
    }

    /**
     * Applique le filtre de sécurité (helper)
     */
    applySecurityFilter() {
        const securityFilter = document.getElementById('filter-security').value;
        this.filterBySecurity(securityFilter);
    }

    /**
     * Recherche de buckets
     */
    searchBuckets(query) {
        const regionFilter = document.getElementById('filter-region').value;
        const securityFilter = document.getElementById('filter-security').value;

        // Réappliquer tous les filtres
        this.filterByRegion(regionFilter);
        this.filterBySecurity(securityFilter);

        // Puis appliquer la recherche
        if (query.trim() !== '') {
            const lowerQuery = query.toLowerCase();
            this.filteredBuckets = this.filteredBuckets.filter(bucket =>
                bucket.bucket_name.toLowerCase().includes(lowerQuery)
            );
        }

        this.updateBucketsTable();
    }

    /**
     * Applique le filtre de recherche (helper)
     */
    applySearchFilter() {
        const searchQuery = document.getElementById('search-buckets').value;
        if (searchQuery.trim() !== '') {
            const lowerQuery = searchQuery.toLowerCase();
            this.filteredBuckets = this.filteredBuckets.filter(bucket =>
                bucket.bucket_name.toLowerCase().includes(lowerQuery)
            );
        }
        this.updateBucketsTable();
    }

    /**
     * Configure les event listeners
     */
    setupEventListeners() {
        // Bouton rafraîchir
        document.getElementById('refresh-btn').addEventListener('click', () => this.refresh());

        // Filtres
        document.getElementById('filter-region').addEventListener('change', (e) => this.filterByRegion(e.target.value));
        document.getElementById('filter-security').addEventListener('change', (e) => this.filterBySecurity(e.target.value));

        // Recherche
        document.getElementById('search-buckets').addEventListener('input', (e) => this.searchBuckets(e.target.value));

        // Modal
        document.getElementById('close-modal').addEventListener('click', () => this.closeBucketModal());
        document.getElementById('bucket-modal').addEventListener('click', (e) => {
            if (e.target.id === 'bucket-modal') {
                this.closeBucketModal();
            }
        });
    }

    /**
     * Rafraîchit le dashboard
     */
    async refresh() {
        console.log('🔄 Rafraîchissement du dashboard S3...');
        await this.init();
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
     * Ouvre le modal avec les détails d'un bucket
     */
    openBucketModal(bucket) {
        const modal = document.getElementById('bucket-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('modal-content');

        // Titre
        modalTitle.textContent = `Détails : ${bucket.bucket_name}`;

        // Contenu
        modalContent.innerHTML = this.generateModalContent(bucket);

        // Afficher le modal
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    /**
     * Ferme le modal
     */
    closeBucketModal() {
        const modal = document.getElementById('bucket-modal');
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }

    /**
     * Génère le contenu HTML du modal
     */
    generateModalContent(bucket) {
        const creationDate = bucket.creation_date
            ? new Date(bucket.creation_date).toLocaleString('fr-FR')
            : '-';
        const scanTime = bucket.scan_timestamp
            ? new Date(bucket.scan_timestamp).toLocaleString('fr-FR')
            : '-';

        return `
            <!-- Section: Informations Générales -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-blue-400">info</span>
                    Informations Générales
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Bucket Name</p>
                        <p class="text-white font-medium">${bucket.bucket_name}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Région</p>
                        <p class="text-white font-medium">${bucket.region}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Créé le</p>
                        <p class="text-white text-sm">${creationDate}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Dernier scan</p>
                        <p class="text-white text-sm">${scanTime}</p>
                    </div>
                </div>
            </div>

            <!-- Section: Configuration de Sécurité -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-blue-400">security</span>
                    Configuration de Sécurité
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg flex items-center justify-between">
                        <span class="text-slate-400 text-sm">Encryption</span>
                        ${this.getBooleanBadge(bucket.encryption_enabled)}
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg flex items-center justify-between">
                        <span class="text-slate-400 text-sm">Versioning</span>
                        ${this.getBooleanBadge(bucket.versioning_enabled)}
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg flex items-center justify-between">
                        <span class="text-slate-400 text-sm">Public Access Blocked</span>
                        ${this.getBooleanBadge(bucket.public_access_blocked)}
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg flex items-center justify-between">
                        <span class="text-slate-400 text-sm">Public Read Enabled</span>
                        ${this.getBooleanBadge(bucket.public_read_enabled)}
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg flex items-center justify-between">
                        <span class="text-slate-400 text-sm">Bucket Policy</span>
                        ${this.getBooleanBadge(bucket.bucket_policy_enabled)}
                    </div>
                </div>
            </div>

            <!-- Section: Fonctionnalités Avancées -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-blue-400">tune</span>
                    Fonctionnalités Avancées
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg flex items-center justify-between">
                        <span class="text-slate-400 text-sm">Lifecycle Rules</span>
                        ${this.getBooleanBadge(bucket.lifecycle_enabled)}
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg flex items-center justify-between">
                        <span class="text-slate-400 text-sm">CORS</span>
                        ${this.getBooleanBadge(bucket.cors_enabled)}
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg flex items-center justify-between">
                        <span class="text-slate-400 text-sm">Website Hosting</span>
                        ${this.getBooleanBadge(bucket.website_enabled)}
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg flex items-center justify-between">
                        <span class="text-slate-400 text-sm">Logging</span>
                        ${this.getBooleanBadge(bucket.logging_enabled)}
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg flex items-center justify-between">
                        <span class="text-slate-400 text-sm">Notifications</span>
                        ${this.getBooleanBadge(bucket.notifications_enabled)}
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg flex items-center justify-between">
                        <span class="text-slate-400 text-sm">Replication</span>
                        ${this.getBooleanBadge(bucket.replication_enabled)}
                    </div>
                </div>
            </div>

            <!-- Section: Métriques de Performance (24h) -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-blue-400">speed</span>
                    Métriques de Performance (24h)
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Total Requests</p>
                        <p class="text-white font-medium text-lg">
                            ${bucket.performance?.all_requests?.toLocaleString() || '-'}
                        </p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">GET Requests</p>
                        <p class="text-white font-medium text-lg">
                            ${bucket.performance?.get_requests?.toLocaleString() || '-'}
                        </p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">PUT Requests</p>
                        <p class="text-white font-medium text-lg">
                            ${bucket.performance?.put_requests?.toLocaleString() || '-'}
                        </p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">DELETE Requests</p>
                        <p class="text-white font-medium text-lg">
                            ${bucket.performance?.delete_requests?.toLocaleString() || '-'}
                        </p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">4xx Errors</p>
                        <p class="text-white font-medium text-lg">
                            ${bucket.performance?.errors_4xx?.toLocaleString() || '-'}
                        </p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">5xx Errors</p>
                        <p class="text-white font-medium text-lg">
                            ${bucket.performance?.errors_5xx?.toLocaleString() || '-'}
                        </p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">First Byte Latency (avg)</p>
                        <p class="text-white font-medium text-lg">
                            ${bucket.performance?.first_byte_latency_avg ? bucket.performance.first_byte_latency_avg + ' ms' : '-'}
                        </p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Total Request Latency (avg)</p>
                        <p class="text-white font-medium text-lg">
                            ${bucket.performance?.total_request_latency_avg ? bucket.performance.total_request_latency_avg + ' ms' : '-'}
                        </p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Bytes Downloaded</p>
                        <p class="text-white font-medium text-lg">
                            ${s3Stats.formatBytes(bucket.performance?.bytes_downloaded || 0)}
                        </p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Bytes Uploaded</p>
                        <p class="text-white font-medium text-lg">
                            ${s3Stats.formatBytes(bucket.performance?.bytes_uploaded || 0)}
                        </p>
                    </div>
                </div>
            </div>
        `;
    }
}

// Initialiser au chargement
const dashboardS3 = new DashboardS3();
document.addEventListener('DOMContentLoaded', () => dashboardS3.init());

