/**
 * Dashboard VPC - Gestion de l'affichage et des graphiques
 */

class DashboardVPC {
    constructor() {
        this.vpcStats = new VPCStats();
        this.charts = {};
        this.currentRegionFilter = 'all';
    }

    /**
     * Initialise le dashboard
     */
    async init() {
        try {
            console.log('🚀 Initialisation du dashboard VPC...');

            // Afficher le loader
            this.showLoader();

            // Charger les données
            console.log('📡 Chargement des VPCs depuis l\'API...');
            await this.vpcStats.loadVPCs({ limit: 100 });
            console.log(`✅ ${this.vpcStats.vpcs.length} VPCs chargés`);

            // Masquer le loader
            this.hideLoader();

            // Vérifier s'il y a des données
            if (this.vpcStats.vpcs.length === 0) {
                console.warn('⚠️ Aucun VPC trouvé');
                this.showNoDataMessage();
                return;
            }

            // Afficher les statistiques
            console.log('📊 Affichage des statistiques...');
            this.displayStats();

            // Créer les graphiques
            console.log('📈 Création des graphiques...');
            this.createCharts();

            // Afficher le tableau
            console.log('📋 Affichage du tableau...');
            this.displayVPCsTable();

            // Initialiser les filtres
            console.log('🔧 Initialisation des filtres...');
            this.initializeFilters();

            console.log('✅ Dashboard VPC initialisé avec succès');

        } catch (error) {
            console.error('❌ Erreur lors de l\'initialisation du dashboard VPC:', error);
            this.hideLoader();
            this.showError('Impossible de charger les données VPC');
        }
    }

    /**
     * Affiche un message quand il n'y a pas de données
     */
    showNoDataMessage() {
        // Masquer les graphiques et le tableau
        const chartsSection = document.querySelector('.grid.grid-cols-1.lg\\:grid-cols-2');
        if (chartsSection) {
            chartsSection.style.display = 'none';
        }

        // Créer le message
        const mainContent = document.querySelector('main');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'glass-card rounded-xl p-12 text-center mt-8';
        messageDiv.innerHTML = `
            <div class="flex flex-col items-center justify-center">
                <span class="material-symbols-outlined text-blue-400 text-6xl mb-4">cloud_off</span>
                <h3 class="text-2xl font-bold text-gray-200 mb-2">Aucun VPC trouvé</h3>
                <p class="text-gray-400 mb-6">Lancez un scan VPC pour commencer à analyser vos réseaux virtuels AWS.</p>
                <a href="config-scan-new.html" class="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors">
                    Configurer un scan
                </a>
            </div>
        `;

        // Insérer après les cartes de stats
        const statsCards = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-4');
        if (statsCards && statsCards.nextSibling) {
            mainContent.insertBefore(messageDiv, statsCards.nextSibling);
        } else {
            mainContent.appendChild(messageDiv);
        }
    }

    /**
     * Affiche les statistiques dans les cartes
     */
    displayStats() {
        const totalStats = this.vpcStats.getTotalVPCsStats();
        const securityStats = this.vpcStats.getSecurityStats();
        const connectivityStats = this.vpcStats.getConnectivityStats();
        const regions = this.vpcStats.getActiveRegions();

        // Carte 1: Total VPCs
        document.getElementById('total-vpcs').textContent = totalStats.total;

        // Carte 2: Régions actives
        document.getElementById('active-regions').textContent = regions.length;

        // Carte 3: Total Subnets
        document.getElementById('total-subnets').textContent = totalStats.totalSubnets;

        // Carte 4: Score de sécurité
        document.getElementById('security-score').textContent = `${securityStats.securityScore}%`;
    }

    /**
     * Crée les graphiques Chart.js
     */
    createCharts() {
        this.createSubnetDistributionChart();
        this.createRegionDistributionChart();
        // TODO: Ajouter createSecurityChart() et createConnectivityChart()
    }

    /**
     * Graphique: Distribution des subnets (Public vs Privé) - Style EC2
     */
    createSubnetDistributionChart() {
        const ctx = document.getElementById('subnet-distribution-chart');
        if (!ctx) return;

        const distribution = this.vpcStats.getSubnetDistribution();

        // Détruire le graphique existant si présent
        if (this.charts.subnetDistribution) {
            this.charts.subnetDistribution.destroy();
        }

        this.charts.subnetDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Subnets Publics', 'Subnets Privés'],
                datasets: [{
                    data: [distribution.public, distribution.private],
                    backgroundColor: [
                        '#137FEC',  // Bleu primary
                        '#8B5CF6'   // Violet secondary
                    ],
                    borderWidth: 0,  // Pas de bordure
                    hoverBorderWidth: 0,
                    hoverOffset: 15,  // Effet hover moderne
                    spacing: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',  // Donut plus fin et moderne
                layout: {
                    padding: 20
                },
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#e2e8f0',
                            padding: 15,
                            font: {
                                size: 13,
                                family: 'Rajdhani',
                                weight: '500'
                            },
                            usePointStyle: true,
                            pointStyle: 'circle',
                            boxWidth: 10,
                            boxHeight: 10
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                        titleColor: '#e5e7eb',
                        bodyColor: '#e5e7eb',
                        borderColor: 'rgba(59, 130, 246, 0.5)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Graphique: VPCs par région
     */
    createRegionDistributionChart() {
        const ctx = document.getElementById('region-distribution-chart');
        if (!ctx) return;

        const regionsStats = this.vpcStats.getRegionsStats();
        const regions = Object.keys(regionsStats);
        const counts = regions.map(region => regionsStats[region].count);

        // Détruire le graphique existant si présent
        if (this.charts.regionDistribution) {
            this.charts.regionDistribution.destroy();
        }

        this.charts.regionDistribution = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: regions,
                datasets: [{
                    label: 'Nombre de VPCs',
                    data: counts,
                    backgroundColor: 'rgba(251, 146, 60, 0.85)',  // Orange VPC pour cohérence
                    borderColor: 'rgba(251, 146, 60, 1)',
                    borderWidth: 2,
                    borderRadius: 8,  // Coins arrondis modernes
                    barThickness: 30  // Largeur fixe pour cohérence
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.98)',
                        titleColor: '#137FEC',
                        bodyColor: '#e2e8f0',
                        borderColor: '#fb923c',
                        borderWidth: 1,
                        padding: 16,
                        displayColors: false,
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
                                const value = context.parsed.y || 0;
                                return ` ${value} VPC${value > 1 ? 's' : ''}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#cbd5e1',
                            font: {
                                size: 12,
                                family: 'Rajdhani'
                            },
                            stepSize: 1
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)',
                            drawBorder: false
                        }
                    },
                    x: {
                        ticks: {
                            color: '#fff',
                            font: {
                                size: 13,
                                weight: '500',
                                family: 'Rajdhani'
                            }
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                },
                animation: {
                    duration: 800,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }

    /**
     * Affiche le tableau des VPCs
     */
    displayVPCsTable() {
        const tbody = document.getElementById('vpcs-table-body');
        if (!tbody) return;

        const vpcs = this.vpcStats.filterByRegion(this.currentRegionFilter);

        if (vpcs.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="px-6 py-8 text-center text-gray-400">
                        <div class="flex flex-col items-center">
                            <span class="material-symbols-outlined text-5xl mb-3">cloud_off</span>
                            <p class="text-lg">Aucun VPC trouvé</p>
                            <p class="text-sm mt-2">Lancez un scan pour commencer</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = '';
        vpcs.forEach(vpc => {
            const row = document.createElement('tr');
            row.className = 'border-b border-gray-700 hover:bg-gray-800/50 transition-colors cursor-pointer';
            row.innerHTML = `
                <td class="px-6 py-4">
                    <span class="font-mono text-blue-400">${vpc.vpc_id}</span>
                </td>
                <td class="px-6 py-4">
                    <span class="font-mono text-gray-300">${vpc.cidr_block || 'N/A'}</span>
                </td>
                <td class="px-6 py-4">
                    <span class="px-2 py-1 rounded text-xs ${vpc.state === 'available' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}">
                        ${vpc.state || 'unknown'}
                    </span>
                </td>
                <td class="px-6 py-4 text-gray-300">${vpc.region || 'N/A'}</td>
                <td class="px-6 py-4 text-center">
                    <div class="flex flex-col items-center gap-1">
                        <span class="text-white font-semibold">${vpc.subnet_count || 0}</span>
                        <div class="flex gap-2 text-xs">
                            <span class="text-blue-400">🌐 ${vpc.public_subnets_count || 0}</span>
                            <span class="text-purple-400">🔒 ${vpc.private_subnets_count || 0}</span>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 text-center">
                    ${vpc.internet_gateway_attached ?
                        '<span class="material-symbols-outlined text-green-400">check_circle</span>' :
                        '<span class="material-symbols-outlined text-gray-600">cancel</span>'}
                </td>
                <td class="px-6 py-4 text-center">
                    ${vpc.flow_logs_enabled ?
                        '<span class="material-symbols-outlined text-green-400">verified_user</span>' :
                        '<span class="material-symbols-outlined text-red-400">warning</span>'}
                </td>
                <td class="px-6 py-4 text-center text-gray-300">${vpc.security_groups_count || 0}</td>
            `;

            // Event listener pour ouvrir le modal
            row.addEventListener('click', () => this.openVPCModal(vpc));

            tbody.appendChild(row);
        });
    }

    /**
     * Initialise les filtres
     */
    initializeFilters() {
        const regionFilter = document.getElementById('region-filter');
        if (regionFilter) {
            // Peupler le filtre de région
            const regions = this.vpcStats.getActiveRegions();
            regionFilter.innerHTML = '<option value="all">Toutes les régions</option>' +
                regions.map(region => `<option value="${region}">${region}</option>`).join('');

            // Écouter les changements
            regionFilter.addEventListener('change', (e) => {
                this.currentRegionFilter = e.target.value;
                this.displayVPCsTable();
            });
        }

        // Bouton refresh
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.init());
        }

        // Fermer le modal
        const closeModalBtn = document.getElementById('close-modal');
        const modal = document.getElementById('instance-modal');

        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', () => this.closeVPCModal());
        }

        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target.id === 'instance-modal') {
                    this.closeVPCModal();
                }
            });
        }
    }

    /**
     * Ouvre le modal avec les détails d'un VPC
     */
    openVPCModal(vpc) {
        const modal = document.getElementById('instance-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('modal-content');

        // Titre
        const vpcName = vpc.tags?.Name || vpc.vpc_id;
        modalTitle.textContent = `Détails : ${vpcName}`;

        // Contenu
        modalContent.innerHTML = this.generateVPCModalContent(vpc);

        // Afficher le modal
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    /**
     * Ferme le modal
     */
    closeVPCModal() {
        const modal = document.getElementById('instance-modal');
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }

    /**
     * Génère le contenu HTML du modal pour un VPC
     */
    generateVPCModalContent(vpc) {
        const scanTime = vpc.scan_timestamp
            ? new Date(vpc.scan_timestamp).toLocaleString('fr-FR')
            : '-';

        // Parser les tags (peuvent être string ou objet)
        let tagsObj = {};
        if (vpc.tags) {
            if (typeof vpc.tags === 'string') {
                // Format: "Key1=Value1,Key2=Value2"
                vpc.tags.split(',').forEach(tag => {
                    const [key, value] = tag.split('=');
                    if (key && value) {
                        tagsObj[key.trim()] = value.trim();
                    }
                });
            } else if (typeof vpc.tags === 'object') {
                tagsObj = vpc.tags;
            }
        }

        const tagsHtml = Object.keys(tagsObj).length > 0
            ? Object.entries(tagsObj).map(([key, value]) => `
                <div class="flex items-center gap-2 bg-slate-800/40 px-3 py-2 rounded-lg">
                    <span class="text-slate-400 text-sm">${key}:</span>
                    <span class="text-white text-sm font-medium">${value}</span>
                </div>
            `).join('')
            : '<p class="text-slate-400 text-sm">Aucun tag</p>';

        // Subnets - Afficher les statistiques (pas de détails disponibles dans l'API)
        const totalSubnets = vpc.subnet_count || 0;
        const publicSubnets = vpc.public_subnets_count || 0;
        const privateSubnets = vpc.private_subnets_count || 0;
        const azs = vpc.availability_zones || [];

        const subnetsHtml = totalSubnets > 0
            ? `
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg text-center">
                        <p class="text-slate-400 text-xs mb-1">Total</p>
                        <p class="text-white text-2xl font-bold">${totalSubnets}</p>
                    </div>
                    <div class="bg-blue-500/10 border border-blue-500/30 px-4 py-3 rounded-lg text-center">
                        <p class="text-blue-400 text-xs mb-1">🌐 Public</p>
                        <p class="text-blue-400 text-2xl font-bold">${publicSubnets}</p>
                    </div>
                    <div class="bg-purple-500/10 border border-purple-500/30 px-4 py-3 rounded-lg text-center">
                        <p class="text-purple-400 text-xs mb-1">🔒 Privé</p>
                        <p class="text-purple-400 text-2xl font-bold">${privateSubnets}</p>
                    </div>
                </div>
                ${azs.length > 0 ? `
                    <div class="mt-3 bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-2">Availability Zones</p>
                        <div class="flex flex-wrap gap-2">
                            ${azs.map(az => `<span class="px-2 py-1 bg-cyan-500/20 text-cyan-400 text-xs rounded">${az}</span>`).join('')}
                        </div>
                    </div>
                ` : ''}
            `
            : '<p class="text-slate-400 text-sm">Aucun subnet</p>';

        // Security Groups - Afficher le compteur
        const sgCount = vpc.security_groups_count || 0;
        const securityGroupsHtml = `
            <div class="bg-slate-800/40 px-4 py-3 rounded-lg text-center">
                <p class="text-slate-400 text-xs mb-1">Security Groups</p>
                <p class="text-white text-2xl font-bold">${sgCount}</p>
            </div>
        `;

        // État du VPC
        const stateColor = vpc.state === 'available' ? 'text-green-400' : 'text-yellow-400';
        const stateIcon = vpc.state === 'available' ? '🟢' : '🟡';

        return `
            <!-- Informations Générales -->
            <div class="bg-slate-800/30 rounded-xl p-6 border border-slate-700/50">
                <h4 class="text-white text-lg font-semibold mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-orange-400">cloud</span>
                    Informations Générales
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <p class="text-slate-400 text-sm">VPC ID</p>
                        <p class="text-white font-medium">${vpc.vpc_id}</p>
                    </div>
                    <div>
                        <p class="text-slate-400 text-sm">Région</p>
                        <p class="text-white font-medium">${vpc.region}</p>
                    </div>
                    <div>
                        <p class="text-slate-400 text-sm">CIDR Block</p>
                        <p class="text-white font-medium">${vpc.cidr_block}</p>
                    </div>
                    <div>
                        <p class="text-slate-400 text-sm">État</p>
                        <p class="${stateColor} font-medium">${stateIcon} ${vpc.state}</p>
                    </div>
                    <div>
                        <p class="text-slate-400 text-sm">VPC par défaut</p>
                        <p class="text-white font-medium">${vpc.is_default ? '✅ Oui' : '❌ Non'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400 text-sm">Tenancy</p>
                        <p class="text-white font-medium">${vpc.tenancy || 'default'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400 text-sm">Internet Gateway</p>
                        <p class="text-white font-medium">${vpc.internet_gateway_attached ? '✅ Attaché' : '❌ Non attaché'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400 text-sm">Scanné le</p>
                        <p class="text-white font-medium">${scanTime}</p>
                    </div>
                </div>
            </div>

            <!-- Tags -->
            <div class="bg-slate-800/30 rounded-xl p-6 border border-slate-700/50">
                <h4 class="text-white text-lg font-semibold mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-cyan-400">label</span>
                    Tags
                </h4>
                <div class="flex flex-wrap gap-2">
                    ${tagsHtml}
                </div>
            </div>

            <!-- Subnets -->
            <div class="bg-slate-800/30 rounded-xl p-6 border border-slate-700/50">
                <h4 class="text-white text-lg font-semibold mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-blue-400">lan</span>
                    Subnets (${totalSubnets})
                </h4>
                ${subnetsHtml}
            </div>

            <!-- Ressources Réseau -->
            <div class="bg-slate-800/30 rounded-xl p-6 border border-slate-700/50">
                <h4 class="text-white text-lg font-semibold mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-red-400">shield</span>
                    Ressources Réseau
                </h4>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    ${securityGroupsHtml}
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg text-center">
                        <p class="text-slate-400 text-xs mb-1">Network ACLs</p>
                        <p class="text-white text-2xl font-bold">${vpc.network_acls_count || 0}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg text-center">
                        <p class="text-slate-400 text-xs mb-1">Route Tables</p>
                        <p class="text-white text-2xl font-bold">${vpc.route_tables_count || 0}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg text-center">
                        <p class="text-slate-400 text-xs mb-1">NAT Gateways</p>
                        <p class="text-white text-2xl font-bold">${vpc.nat_gateways_count || 0}</p>
                    </div>
                </div>
            </div>

            <!-- Sécurité & Connectivité -->
            <div class="bg-slate-800/30 rounded-xl p-6 border border-slate-700/50">
                <h4 class="text-white text-lg font-semibold mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-green-400">security</span>
                    Sécurité & Connectivité
                </h4>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Flow Logs</p>
                        <p class="text-white font-medium">${vpc.flow_logs_enabled ? '✅ Activé' : '❌ Désactivé'}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">VPC Endpoints</p>
                        <p class="text-white font-medium">${vpc.vpc_endpoints_count || 0}</p>
                    </div>
                    <div class="bg-slate-800/40 px-4 py-3 rounded-lg">
                        <p class="text-slate-400 text-xs mb-1">Peering Connections</p>
                        <p class="text-white font-medium">${vpc.vpc_peering_connections_count || 0}</p>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Affiche le loader
     */
    showLoader() {
        const loader = document.getElementById('loader');
        if (loader) loader.classList.remove('hidden');
    }

    /**
     * Masque le loader
     */
    hideLoader() {
        const loader = document.getElementById('loader');
        if (loader) loader.classList.add('hidden');
    }

    /**
     * Affiche un message d'erreur
     */
    showError(message) {
        console.error(message);
        // Vous pouvez ajouter une notification toast ici
    }
}
