/**
 * Dashboard EC2 - Gestion de l'affichage
 */

class DashboardEC2 {
    constructor() {
        this.charts = {};
        this.filteredInstances = [];
    }

    /**
     * Initialise le dashboard
     */
    async init() {
        // Éviter les initialisations multiples
        if (this.isInitializing || this.isInitialized) {
            console.warn('⚠️ Dashboard déjà en cours d\'initialisation ou initialisé');
            return;
        }

        this.isInitializing = true;
        console.log('🚀 Initialisation du dashboard EC2...');
        this.showLoader();

        try {
            // Charger les instances
            const instances = await ec2Stats.loadInstances();

            // Vérifier s'il y a des données
            if (!instances || instances.length === 0) {
                this.hideLoader();
                this.isInitializing = false;
                this.showInfo('Aucune instance EC2 trouvée. Lancez un scan pour commencer.');
                return;
            }

            // Mettre à jour l'interface
            this.updateStatsCards();
            this.createCharts();
            this.updateAlertsSection();
            this.updateInstancesTable();

            // Event listeners
            this.setupEventListeners();

            this.hideLoader();
            this.isInitializing = false;
            this.isInitialized = true;
            console.log('✅ Dashboard EC2 chargé avec succès');
        } catch (error) {
            console.error('❌ Erreur chargement dashboard:', error);
            this.hideLoader();
            this.isInitializing = false;
            this.showError('Erreur lors du chargement des données EC2');
        }
    }

    /**
     * Met à jour les cartes de statistiques
     */
    updateStatsCards() {
        // Card 1: Total Instances
        const totalStats = ec2Stats.getTotalInstancesStats();
        document.getElementById('total-instances').textContent = totalStats.total;
        document.getElementById('instances-detail').textContent =
            `${totalStats.running} running, ${totalStats.stopped} stopped`;

        // Card 2: Régions
        const regionsStats = ec2Stats.getRegionsStats();
        document.getElementById('active-regions').textContent = regionsStats.totalRegions;
        document.getElementById('regions-detail').textContent =
            regionsStats.topRegion ? `${regionsStats.topRegion} (${regionsStats.topRegionCount})` : 'Régions AWS';

        // Card 3: CPU Moyen
        const cpuStats = ec2Stats.getAverageCPU();
        document.getElementById('avg-cpu').textContent = `${cpuStats.average}%`;
        document.getElementById('cpu-detail').textContent =
            `Min: ${cpuStats.min}% | Max: ${cpuStats.max}%`;

        // Card 4: Trafic Réseau
        const trafficStats = ec2Stats.getNetworkTrafficStats();
        document.getElementById('total-network').textContent = trafficStats.totalFormatted;
        document.getElementById('network-detail').textContent =
            `${trafficStats.inFormatted} IN | ${trafficStats.outFormatted} OUT`;

        console.log('✅ Stats cards mises à jour');
    }

    /**
     * Crée les graphiques Chart.js
     */
    createCharts() {
        this.createInstanceTypesChart();
        this.createInstanceStatesChart();
        this.createCPUChart();
        this.createNetworkChart();
        console.log('✅ Graphiques créés');
    }

    /**
     * Graphique: Répartition par type (Donut)
     */
    createInstanceTypesChart() {
        const ctx = document.getElementById('chart-instance-types');
        const data = ec2Stats.getInstanceTypeDistribution();

        if (this.charts.types) this.charts.types.destroy();

        this.charts.types = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.data,
                    backgroundColor: [
                        '#137fec', '#4285F4', '#0078D4', '#FF9900',
                        '#34A853', '#EA4335', '#FBBC04', '#9333EA'
                    ],
                    borderWidth: 3,
                    borderColor: '#0a0e1a',
                    hoverBorderWidth: 5,
                    hoverBorderColor: '#ffffff',
                    offset: 5,
                    spacing: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: 10
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#cbd5e1', padding: 15, font: { size: 12 } }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#137fec',
                        bodyColor: '#cbd5e1',
                        borderColor: '#137fec',
                        borderWidth: 2,
                        padding: 12,
                        displayColors: true,
                        boxWidth: 15,
                        boxHeight: 15
                    }
                },
                elements: {
                    arc: {
                        borderRadius: 6
                    }
                }
            }
        });
    }

    /**
     * Graphique: Répartition par état (Bar)
     */
    createInstanceStatesChart() {
        const ctx = document.getElementById('chart-instance-states');
        const data = ec2Stats.getStateDistribution();

        if (this.charts.states) this.charts.states.destroy();

        const colors = {
            'running': '#34A853',
            'stopped': '#FBBC04',
            'terminated': '#EA4335',
            'pending': '#4285F4',
            'stopping': '#FF9900'
        };

        const backgroundColors = data.labels.map(label => colors[label] || '#137fec');

        this.charts.states = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Instances',
                    data: data.data,
                    backgroundColor: backgroundColors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#cbd5e1', stepSize: 1 },
                        grid: { color: 'rgba(203, 213, 225, 0.1)' }
                    },
                    x: {
                        ticks: { color: '#cbd5e1' },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Graphique: CPU par instance (Bar Horizontal)
     */
    createCPUChart() {
        const ctx = document.getElementById('chart-cpu-instances');
        const data = ec2Stats.getCPUByInstance();

        if (this.charts.cpu) this.charts.cpu.destroy();

        this.charts.cpu = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'CPU (%)',
                    data: data.data,
                    backgroundColor: '#137fec',
                    borderWidth: 0
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { color: '#cbd5e1' },
                        grid: { color: 'rgba(203, 213, 225, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#cbd5e1' },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Graphique: Trafic réseau par instance (Stacked Bar)
     */
    createNetworkChart() {
        const ctx = document.getElementById('chart-network-instances');
        const data = ec2Stats.getNetworkByInstance();

        if (this.charts.network) this.charts.network.destroy();

        this.charts.network = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Trafic IN (bytes)',
                        data: data.dataIn,
                        backgroundColor: '#34A853',
                        borderWidth: 0
                    },
                    {
                        label: 'Trafic OUT (bytes)',
                        data: data.dataOut,
                        backgroundColor: '#EA4335',
                        borderWidth: 0
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#cbd5e1', padding: 15 }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        ticks: { color: '#cbd5e1' },
                        grid: { color: 'rgba(203, 213, 225, 0.1)' }
                    },
                    y: {
                        stacked: true,
                        ticks: { color: '#cbd5e1' },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Met à jour la section alertes
     */
    updateAlertsSection() {
        const alerts = ec2Stats.getAlerts();
        const section = document.getElementById('alerts-section');
        const container = document.getElementById('alerts-container');

        if (alerts.length === 0) {
            section.classList.add('hidden');
            return;
        }

        section.classList.remove('hidden');
        container.innerHTML = '';

        const iconMap = {
            'critical': { icon: 'error', color: 'red' },
            'warning': { icon: 'warning', color: 'yellow' },
            'info': { icon: 'info', color: 'blue' }
        };

        alerts.forEach(alert => {
            const config = iconMap[alert.type] || iconMap.info;
            const div = document.createElement('div');
            div.className = 'flex items-start gap-3 rounded-lg bg-slate-800/40 p-3';
            div.innerHTML = `
                <div class="flex h-8 w-8 items-center justify-center rounded-full bg-${config.color}-500/20 text-${config.color}-400">
                    <span class="material-symbols-outlined text-lg">${config.icon}</span>
                </div>
                <div class="flex-1">
                    <p class="font-medium text-white">${alert.message}</p>
                </div>
            `;
            container.appendChild(div);
        });

        console.log(`✅ ${alerts.length} alertes affichées`);
    }

    /**
     * Met à jour le tableau des instances
     */
    updateInstancesTable() {
        this.filteredInstances = ec2Stats.instances;
        this.renderInstancesTable();
    }

    /**
     * Affiche le tableau des instances
     */
    renderInstancesTable() {
        const tbody = document.getElementById('instances-table-body');
        const noInstances = document.getElementById('no-instances');

        if (this.filteredInstances.length === 0) {
            tbody.innerHTML = '';
            noInstances.classList.remove('hidden');
            return;
        }

        noInstances.classList.add('hidden');
        tbody.innerHTML = '';

        this.filteredInstances.forEach(instance => {
            const row = document.createElement('tr');
            row.className = 'border-b border-slate-800 hover:bg-slate-800/30 cursor-pointer';
            row.dataset.instanceId = instance.instance_id;

            const stateBadge = this.getStateBadge(instance.state);
            const name = instance.tags?.Name || '-';
            const cpu = instance.performance?.cpu_utilization_avg
                ? `${instance.performance.cpu_utilization_avg.toFixed(2)}%`
                : '-';
            const traffic = instance.performance
                ? ec2Stats.formatBytes((instance.performance.network_in_bytes || 0) + (instance.performance.network_out_bytes || 0))
                : '-';
            const launchTime = instance.launch_time
                ? new Date(instance.launch_time).toLocaleDateString('fr-FR', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                })
                : '-';

            row.innerHTML = `
                <td class="py-3">${name}</td>
                <td class="py-3 font-mono text-xs">${instance.instance_id}</td>
                <td class="py-3">${instance.instance_type}</td>
                <td class="py-3">${stateBadge}</td>
                <td class="py-3">${instance.region}</td>
                <td class="py-3 font-mono text-xs">${instance.public_ip || '-'}</td>
                <td class="py-3 font-mono text-xs">${instance.private_ip || '-'}</td>
                <td class="py-3">${cpu}</td>
                <td class="py-3">${traffic}</td>
                <td class="py-3 text-xs">${launchTime}</td>
            `;

            // Event listener pour ouvrir le modal
            row.addEventListener('click', () => this.openInstanceModal(instance));

            tbody.appendChild(row);
        });

        console.log(`✅ ${this.filteredInstances.length} instances affichées dans le tableau`);
    }

    /**
     * Retourne un badge HTML pour l'état
     */
    getStateBadge(state) {
        const badges = {
            'running': '<span class="px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs">🟢 running</span>',
            'stopped': '<span class="px-2 py-1 rounded-full bg-yellow-500/20 text-yellow-400 text-xs">🟡 stopped</span>',
            'terminated': '<span class="px-2 py-1 rounded-full bg-red-500/20 text-red-400 text-xs">🔴 terminated</span>',
            'pending': '<span class="px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 text-xs">🔵 pending</span>'
        };
        return badges[state] || `<span class="px-2 py-1 rounded-full bg-gray-500/20 text-gray-400 text-xs">${state}</span>`;
    }

    /**
     * Configure les event listeners
     */
    setupEventListeners() {
        // Ne configurer qu'une seule fois
        if (this.listenersAttached) {
            return;
        }

        // Bouton rafraîchir
        document.getElementById('refresh-btn').addEventListener('click', () => this.refresh());

        // Filtre par état
        document.getElementById('filter-state').addEventListener('change', (e) => this.filterByState(e.target.value));

        // Recherche
        document.getElementById('search-instances').addEventListener('input', (e) => this.searchInstances(e.target.value));

        // Fermer le modal
        document.getElementById('close-modal').addEventListener('click', () => this.closeInstanceModal());
        document.getElementById('instance-modal').addEventListener('click', (e) => {
            if (e.target.id === 'instance-modal') {
                this.closeInstanceModal();
            }
        });

        this.listenersAttached = true;
    }

    /**
     * Filtre par état
     */
    filterByState(state) {
        if (state === 'all') {
            this.filteredInstances = ec2Stats.instances;
        } else {
            this.filteredInstances = ec2Stats.instances.filter(i => i.state === state);
        }
        this.renderInstancesTable();
    }

    /**
     * Recherche dans les instances
     */
    searchInstances(query) {
        const lowerQuery = query.toLowerCase();
        this.filteredInstances = ec2Stats.instances.filter(i => 
            (i.tags?.Name || '').toLowerCase().includes(lowerQuery) ||
            i.instance_id.toLowerCase().includes(lowerQuery) ||
            i.instance_type.toLowerCase().includes(lowerQuery)
        );
        this.renderInstancesTable();
    }

    /**
     * Rafraîchit le dashboard
     */
    async refresh() {
        console.log('🔄 Rafraîchissement du dashboard...');
        // Réinitialiser les flags pour permettre un nouveau chargement
        this.isInitialized = false;
        this.isInitializing = false;
        await this.init();
    }

    /**
     * Affiche le loader
     */
    showLoader() {
        document.getElementById('dashboard-loader').classList.remove('hidden');
    }

    /**
     * Masque le loader
     */
    hideLoader() {
        document.getElementById('dashboard-loader').classList.add('hidden');
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
     * Affiche un message d'information
     */
    showInfo(message) {
        const infoDiv = document.createElement('div');
        infoDiv.className = 'fixed top-4 right-4 bg-blue-500/10 border border-blue-500 text-blue-400 px-6 py-4 rounded-lg backdrop-blur-sm z-50';
        infoDiv.innerHTML = `
            <div class="flex items-center gap-3">
                <span class="material-symbols-outlined">info</span>
                <div>
                    <p class="font-bold">${message}</p>
                    <p class="text-sm mt-1">Allez dans <a href="config-scan-new.html" class="underline hover:text-blue-300">Configuration de scan</a> pour lancer un scan.</p>
                </div>
            </div>
        `;
        document.body.appendChild(infoDiv);
        setTimeout(() => infoDiv.remove(), 8000);
    }

    /**
     * Ouvre le modal avec les détails d'une instance
     */
    openInstanceModal(instance) {
        const modal = document.getElementById('instance-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('modal-content');

        // Titre
        const instanceName = instance.tags?.Name || instance.instance_id;
        modalTitle.textContent = `Détails : ${instanceName}`;

        // Contenu
        modalContent.innerHTML = this.generateModalContent(instance);

        // Afficher le modal
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    /**
     * Ferme le modal
     */
    closeInstanceModal() {
        const modal = document.getElementById('instance-modal');
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }

    /**
     * Génère le contenu HTML du modal
     */
    generateModalContent(instance) {
        const launchTime = instance.launch_time
            ? new Date(instance.launch_time).toLocaleString('fr-FR')
            : '-';
        const scanTime = instance.scan_timestamp
            ? new Date(instance.scan_timestamp).toLocaleString('fr-FR')
            : '-';

        // Tags
        const tagsHtml = instance.tags && Object.keys(instance.tags).length > 0
            ? Object.entries(instance.tags).map(([key, value]) => `
                <div class="flex items-center gap-2 bg-slate-800/40 px-3 py-2 rounded-lg">
                    <span class="text-slate-400 text-sm">${key}:</span>
                    <span class="text-white text-sm font-medium">${value}</span>
                </div>
            `).join('')
            : '<p class="text-slate-400 text-sm">Aucun tag</p>';

        // EBS Volumes
        const ebsHtml = instance.ebs_volumes && instance.ebs_volumes.length > 0
            ? instance.ebs_volumes.map(vol => `
                <div class="flex items-center justify-between bg-slate-800/40 px-4 py-3 rounded-lg">
                    <div class="flex items-center gap-3">
                        <span class="material-symbols-outlined text-primary">storage</span>
                        <div>
                            <p class="text-white font-medium">${vol.volume_id}</p>
                            <p class="text-slate-400 text-xs">${vol.device_name}</p>
                        </div>
                    </div>
                    <span class="text-xs ${vol.delete_on_termination ? 'text-red-400' : 'text-green-400'}">
                        ${vol.delete_on_termination ? 'Suppression auto' : 'Persistant'}
                    </span>
                </div>
            `).join('')
            : '<p class="text-slate-400 text-sm">Aucun volume EBS</p>';

        return `
            <!-- Section: Informations Générales -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">info</span>
                    Informations Générales
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Instance ID</p>
                        <p class="text-white font-mono text-sm">${instance.instance_id}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Type</p>
                        <p class="text-white font-medium">${instance.instance_type}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">État</p>
                        <p>${this.getStateBadge(instance.state)}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">AMI ID</p>
                        <p class="text-white font-mono text-sm">${instance.ami_id || '-'}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Lancée le</p>
                        <p class="text-white text-sm">${launchTime}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Dernier scan</p>
                        <p class="text-white text-sm">${scanTime}</p>
                    </div>
                </div>
            </div>

            <!-- Section: Réseau -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">lan</span>
                    Configuration Réseau
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Région</p>
                        <p class="text-white font-medium">${instance.region}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Zone de disponibilité</p>
                        <p class="text-white font-medium">${instance.availability_zone || '-'}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">VPC ID</p>
                        <p class="text-white font-mono text-sm">${instance.vpc_id || '-'}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Subnet ID</p>
                        <p class="text-white font-mono text-sm">${instance.subnet_id || '-'}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">IP Publique</p>
                        <p class="text-white font-mono text-sm">${instance.public_ip || '-'}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">IP Privée</p>
                        <p class="text-white font-mono text-sm">${instance.private_ip || '-'}</p>
                    </div>
                </div>
            </div>

            <!-- Section: Performance -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">speed</span>
                    Métriques de Performance
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">CPU Utilization (avg)</p>
                        <p class="text-white font-medium text-lg">
                            ${instance.performance?.cpu_utilization_avg?.toFixed(2) || '0'}%
                        </p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Memory Utilization (avg)</p>
                        <p class="text-white font-medium text-lg">
                            ${instance.performance?.memory_utilization_avg?.toFixed(2) || '-'}
                        </p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Trafic Entrant</p>
                        <p class="text-white font-medium text-lg">
                            ${ec2Stats.formatBytes(instance.performance?.network_in_bytes || 0)}
                        </p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Trafic Sortant</p>
                        <p class="text-white font-medium text-lg">
                            ${ec2Stats.formatBytes(instance.performance?.network_out_bytes || 0)}
                        </p>
                    </div>
                </div>
            </div>

            <!-- Section: Tags -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">label</span>
                    Tags
                </h4>
                <div class="flex flex-wrap gap-2">
                    ${tagsHtml}
                </div>
            </div>

            <!-- Section: Volumes EBS -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">storage</span>
                    Volumes EBS (${instance.ebs_volumes?.length || 0})
                </h4>
                <div class="space-y-2">
                    ${ebsHtml}
                </div>
            </div>
        `;
    }
}

// Instance globale (initialisée au chargement par le HTML)
const dashboardEC2 = new DashboardEC2();

