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
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2
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
                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                        titleColor: '#e5e7eb',
                        bodyColor: '#e5e7eb',
                        borderColor: 'rgba(59, 130, 246, 0.5)',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#9ca3af',
                            font: {
                                family: 'Rajdhani'
                            }
                        },
                        grid: {
                            color: 'rgba(75, 85, 99, 0.3)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#9ca3af',
                            font: {
                                family: 'Rajdhani'
                            }
                        },
                        grid: {
                            display: false
                        }
                    }
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

        tbody.innerHTML = vpcs.map(vpc => `
            <tr class="border-b border-gray-700 hover:bg-gray-800/50 transition-colors">
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
                    <span class="text-blue-400 font-semibold">${vpc.subnet_count || 0}</span>
                    <span class="text-xs text-gray-500 ml-1">(${vpc.public_subnets_count || 0}/${vpc.private_subnets_count || 0})</span>
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
            </tr>
        `).join('');
    }

    /**
     * Initialise les filtres
     */
    initializeFilters() {
        const regionFilter = document.getElementById('region-filter');
        if (!regionFilter) return;

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
