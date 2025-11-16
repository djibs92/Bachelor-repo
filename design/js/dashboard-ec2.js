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

        // Card 2: Régions - Afficher toutes les régions actives
        const regionsStats = ec2Stats.getRegionsStats();
        document.getElementById('active-regions').textContent = regionsStats.totalRegions;

        // Récupérer toutes les régions uniques
        const allRegions = [...new Set(ec2Stats.instances.map(i => i.region))].sort();
        const regionsText = allRegions.length > 0 ? allRegions.join(', ') : 'Aucune région';
        document.getElementById('regions-detail').textContent = regionsText;

        // Card 3: CPU Moyen
        const cpuStats = ec2Stats.getAverageCPU();
        const cpuElement = document.getElementById('avg-cpu');
        cpuElement.textContent = `${cpuStats.average}%`;
        cpuElement.style.color = this.getColorByPercentage(cpuStats.average);
        document.getElementById('cpu-detail').textContent =
            `Min: ${cpuStats.min}% | Max: ${cpuStats.max}%`;

        // Card 4: Trafic Réseau
        const trafficStats = ec2Stats.getNetworkTrafficStats();
        const networkElement = document.getElementById('total-network');
        networkElement.textContent = trafficStats.totalFormatted;
        // Pour le réseau, on utilise un pourcentage basé sur des seuils réalistes
        const networkPercentage = this.calculateNetworkPercentage(trafficStats.total);
        networkElement.style.color = this.getColorByPercentage(networkPercentage);
        document.getElementById('network-detail').textContent =
            `${trafficStats.inFormatted} IN | ${trafficStats.outFormatted} OUT`;

        console.log('✅ Stats cards mises à jour');
    }

    /**
     * Retourne une couleur selon le pourcentage (vert -> jaune -> orange -> rouge)
     */
    getColorByPercentage(percentage) {
        if (percentage < 30) {
            return '#10b981'; // Vert (low usage)
        } else if (percentage < 50) {
            return '#fbbf24'; // Jaune (moderate)
        } else if (percentage < 75) {
            return '#fb923c'; // Orange (high)
        } else {
            return '#ef4444'; // Rouge (critical)
        }
    }

    /**
     * Calcule un pourcentage pour le trafic réseau basé sur des seuils réalistes
     * < 1 GB = vert, 1-10 GB = jaune, 10-50 GB = orange, > 50 GB = rouge
     */
    calculateNetworkPercentage(bytes) {
        const GB = 1024 * 1024 * 1024;
        const trafficGB = bytes / GB;

        if (trafficGB < 1) {
            return 15; // Vert (< 30%)
        } else if (trafficGB < 10) {
            return 40; // Jaune (30-50%)
        } else if (trafficGB < 50) {
            return 60; // Orange (50-75%)
        } else {
            return 85; // Rouge (> 75%)
        }
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
     * Graphique: Répartition par type (Donut) - Design moderne
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
                        '#137FEC',  // Bleu primary
                        '#8B5CF6',  // Violet secondary
                        '#06B6D4',  // Cyan accent
                        '#10B981',  // Vert success
                        '#F59E0B',  // Orange warning
                        '#EF4444',  // Rouge danger
                        '#EC4899',  // Rose
                        '#6366F1'   // Indigo
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
                                return ` ${label}: ${value} instances (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 1000,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }

    /**
     * Graphique: Répartition par état (Donut avec détails)
     */
    createInstanceStatesChart() {
        const ctx = document.getElementById('chart-instance-states');
        const data = ec2Stats.getStateDistribution();

        if (this.charts.states) this.charts.states.destroy();

        const stateColors = {
            'running': '#22c55e',
            'stopped': '#f59e0b',
            'terminated': '#ef4444',
            'pending': '#3b82f6',
            'stopping': '#f97316',
            'unknown': '#64748b'
        };

        const stateIcons = {
            'running': '▶️',
            'stopped': '⏸️',
            'terminated': '⏹️',
            'pending': '⏳',
            'stopping': '⏬'
        };

        const backgroundColors = data.labels.map(label => stateColors[label] || stateColors['unknown']);

        this.charts.states = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
                datasets: [{
                    data: data.data,
                    backgroundColor: backgroundColors,
                    borderWidth: 0,  // Pas de bordure - qualité parfaite !
                    hoverBorderWidth: 0,
                    hoverOffset: 15,  // Effet hover moderne
                    spacing: 3  // Espacement entre les segments
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
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
                                return ` ${label}: ${value} instances (${percentage}%)`;
                            },
                            afterLabel: function(context) {
                                // Afficher les régions pour cet état
                                const stateLabel = data.labels[context.dataIndex];
                                const regionData = data.byStateAndRegion[stateLabel];

                                if (regionData) {
                                    const regions = Object.entries(regionData)
                                        .sort((a, b) => b[1] - a[1])
                                        .slice(0, 3)
                                        .map(([region, count]) => `  • ${region}: ${count}`)
                                        .join('\n');
                                    return '\nTop Regions:\n' + regions;
                                }
                                return '';
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

        // Créer la légende personnalisée avec détails par région
        this.createStateDetailsLegend(data, stateColors, stateIcons);

        // Mettre à jour le total au centre du donut
        const totalElement = document.getElementById('total-instances-donut');
        if (totalElement) {
            const total = data.data.reduce((a, b) => a + b, 0);
            totalElement.textContent = total;
        }
    }

    /**
     * Crée une légende détaillée pour les états avec répartition par région
     */
    createStateDetailsLegend(data, stateColors, stateIcons) {
        const container = document.getElementById('state-details-legend');
        if (!container) return;

        const total = data.data.reduce((a, b) => a + b, 0);

        let html = '<div class="space-y-3">';

        data.labels.forEach((state, index) => {
            const count = data.data[index];
            const percentage = ((count / total) * 100).toFixed(1);
            const color = stateColors[state] || stateColors['unknown'];
            const icon = stateIcons[state] || '●';
            const regionData = data.byStateAndRegion[state];

            // Trouver les top 3 régions pour cet état
            let regionHtml = '';
            if (regionData) {
                const topRegions = Object.entries(regionData)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 3);

                regionHtml = topRegions.map(([region, regionCount]) =>
                    `<span class="text-xs text-slate-400">${region}: ${regionCount}</span>`
                ).join(' • ');
            }

            html += `
                <div class="flex items-start gap-3 p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition-all cursor-pointer"
                     onmouseover="this.style.transform='translateX(4px)'"
                     onmouseout="this.style.transform='translateX(0)'">
                    <div class="flex items-center gap-2 min-w-[140px]">
                        <div class="w-3 h-3 rounded-full" style="background-color: ${color}; box-shadow: 0 0 8px ${color}50;"></div>
                        <span class="text-white font-medium text-sm">${icon} ${state.charAt(0).toUpperCase() + state.slice(1)}</span>
                    </div>
                    <div class="flex-1">
                        <div class="flex items-center justify-between mb-1">
                            <span class="text-white font-semibold">${count}</span>
                            <span class="text-slate-400 text-xs">${percentage}%</span>
                        </div>
                        <div class="flex flex-wrap gap-2">
                            ${regionHtml}
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * Retourne la couleur en fonction du pourcentage CPU
     * Vert (0-50%) → Jaune (50-75%) → Orange (75-85%) → Rouge (85-100%)
     */
    getCPUColor(cpuValue) {
        if (cpuValue < 50) {
            // Vert → Jaune vert
            const ratio = cpuValue / 50;
            return `rgba(${Math.round(34 + ratio * 186)}, ${Math.round(197 + ratio * 23)}, ${Math.round(94 - ratio * 30)}, 0.8)`;
        } else if (cpuValue < 75) {
            // Jaune → Orange
            const ratio = (cpuValue - 50) / 25;
            return `rgba(${Math.round(234 + ratio * 17)}, ${Math.round(179 - ratio * 64)}, ${Math.round(8 + ratio * 2)}, 0.8)`;
        } else if (cpuValue < 85) {
            // Orange → Rouge orangé
            const ratio = (cpuValue - 75) / 10;
            return `rgba(${Math.round(251 - ratio * 12)}, ${Math.round(146 - ratio * 56)}, ${Math.round(60 - ratio * 36)}, 0.8)`;
        } else {
            // Rouge
            return 'rgba(239, 68, 68, 0.9)';
        }
    }

    /**
     * Graphique: CPU par instance (Bar Horizontal avec couleurs dynamiques)
     */
    createCPUChart() {
        const ctx = document.getElementById('chart-cpu-instances');
        const cpuData = ec2Stats.getCPUByInstance();

        if (this.charts.cpu) this.charts.cpu.destroy();

        // Stocker les données pour le sélecteur
        this.cpuInstancesData = cpuData.instances;

        // Créer les couleurs dynamiques basées sur l'utilisation CPU
        const backgroundColors = cpuData.data.map(cpu => this.getCPUColor(cpu));
        const borderColors = cpuData.data.map(cpu => {
            const color = this.getCPUColor(cpu);
            return color.replace('0.8', '1').replace('0.9', '1');
        });

        this.charts.cpu = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: cpuData.labels,
                datasets: [{
                    label: 'CPU Utilization',
                    data: cpuData.data,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 2,
                    borderRadius: 8,
                    barThickness: 24
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#137FEC',
                        bodyColor: '#cbd5e1',
                        borderColor: '#137FEC',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                const cpu = context.parsed.x;
                                let status = '';
                                if (cpu < 50) status = '✅ Normal';
                                else if (cpu < 75) status = '⚠️ Modéré';
                                else if (cpu < 85) status = '🔶 Élevé';
                                else status = '🔴 Critique';

                                return `CPU: ${cpu.toFixed(2)}% ${status}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: '#64748b',
                            font: { size: 11 },
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(100, 116, 139, 0.1)',
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: '#cbd5e1',
                            font: { size: 11 }
                        },
                        grid: {
                            display: false,
                            drawBorder: false
                        }
                    }
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                }
            }
        });

        // Initialiser le sélecteur d'instance
        this.initCPUInstanceSelector(cpuData.instances);
    }

    /**
     * Initialise le sélecteur d'instance pour le graphique CPU
     */
    initCPUInstanceSelector(instances) {
        const selector = document.getElementById('cpu-instance-selector');
        if (!selector) return;

        // Vider et remplir le sélecteur
        selector.innerHTML = '<option value="all">All Instances (Top 10)</option>';
        instances.forEach((instance, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = instance.name;
            selector.appendChild(option);
        });

        // Event listener pour le changement de sélection
        selector.addEventListener('change', (e) => {
            const selectedValue = e.target.value;
            const chart = this.charts.cpu;
            const cpuData = ec2Stats.getCPUByInstance();

            if (selectedValue === 'all') {
                // Afficher toutes les instances (Top 10)
                chart.data.labels = cpuData.labels;
                chart.data.datasets[0].data = cpuData.data;

                // Recréer les couleurs dynamiques
                chart.data.datasets[0].backgroundColor = cpuData.data.map(cpu => this.getCPUColor(cpu));
                chart.data.datasets[0].borderColor = cpuData.data.map(cpu => {
                    const color = this.getCPUColor(cpu);
                    return color.replace('0.8', '1').replace('0.9', '1');
                });
                chart.data.datasets[0].barThickness = 24;

            } else {
                // Afficher uniquement l'instance sélectionnée
                const selectedIndex = parseInt(selectedValue);
                const selectedInstance = instances[selectedIndex];

                chart.data.labels = [selectedInstance.name];
                chart.data.datasets[0].data = [selectedInstance.cpu];

                // Couleur brillante pour l'instance sélectionnée
                const color = this.getCPUColor(selectedInstance.cpu);
                chart.data.datasets[0].backgroundColor = [color.replace('0.8', '0.95').replace('0.9', '0.95')];
                chart.data.datasets[0].borderColor = [color.replace('0.8', '1').replace('0.9', '1')];
                chart.data.datasets[0].borderWidth = 3;
                chart.data.datasets[0].barThickness = 40;
            }

            chart.update('active'); // Update avec animation
        });

        // Ajouter l'effet de sur-brillance au hover sur les barres
        const canvas = document.getElementById('chart-cpu-instances');
        if (canvas) {
            let lastHoveredIndex = -1;

            canvas.addEventListener('mousemove', (e) => {
                const chart = this.charts.cpu;
                const activeElements = chart.getElementsAtEventForMode(e, 'index', { intersect: false }, false);

                if (activeElements.length > 0 && selector.value === 'all') {
                    const hoveredIndex = activeElements[0].index;

                    // Éviter les updates inutiles
                    if (hoveredIndex !== lastHoveredIndex) {
                        lastHoveredIndex = hoveredIndex;

                        // Appliquer l'effet de sur-brillance sur l'instance survolée
                        const cpuData = ec2Stats.getCPUByInstance();

                        chart.data.datasets[0].backgroundColor = cpuData.data.map((cpu, i) => {
                            const color = this.getCPUColor(cpu);
                            return i === hoveredIndex
                                ? color.replace('0.8', '0.95').replace('0.9', '0.95')
                                : color.replace('0.8', '0.4').replace('0.9', '0.4');
                        });

                        chart.data.datasets[0].borderWidth = cpuData.data.map((_, i) =>
                            i === hoveredIndex ? 3 : 2
                        );

                        chart.update('none');
                    }
                }
            });

            canvas.addEventListener('mouseleave', () => {
                lastHoveredIndex = -1;
                // Restaurer l'état initial quand la souris quitte le canvas
                if (selector.value === 'all') {
                    const cpuData = ec2Stats.getCPUByInstance();
                    this.charts.cpu.data.datasets[0].backgroundColor = cpuData.data.map(cpu => this.getCPUColor(cpu));
                    this.charts.cpu.data.datasets[0].borderWidth = 2;
                    this.charts.cpu.update('none');
                }
            });
        }

        // Déclencher l'état initial (all instances)
        selector.value = 'all';
        selector.dispatchEvent(new Event('change'));
    }

    /**
     * Graphique: Network I/O Monitoring - Affichage IN/OUT par instance
     */
    createNetworkChart() {
        const ctx = document.getElementById('chart-network-instances');
        const networkData = ec2Stats.getNetworkByInstance();

        if (this.charts.network) this.charts.network.destroy();

        // Stocker les données pour le sélecteur
        this.networkInstancesData = networkData.instances;

        // Créer les datasets pour Network IN et Network OUT
        const datasets = [
            {
                label: 'Network IN',
                data: networkData.dataIn,
                backgroundColor: 'rgba(6, 182, 212, 0.7)', // Cyan
                borderColor: '#06b6d4',
                borderWidth: 2,
                borderRadius: 6,
                barThickness: 20
            },
            {
                label: 'Network OUT',
                data: networkData.dataOut,
                backgroundColor: 'rgba(139, 92, 246, 0.7)', // Purple
                borderColor: '#8b5cf6',
                borderWidth: 2,
                borderRadius: 6,
                barThickness: 20
            }
        ];

        this.charts.network = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: networkData.labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: {
                            color: '#cbd5e1',
                            padding: 15,
                            font: { size: 12, weight: '500' },
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#06b6d4',
                        bodyColor: '#cbd5e1',
                        borderColor: '#06b6d4',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                const bytes = context.parsed.y;
                                return `${context.dataset.label}: ${ec2Stats.formatBytes(bytes)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#64748b',
                            font: { size: 11 },
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: {
                            display: false,
                            drawBorder: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#64748b',
                            font: { size: 11 },
                            callback: function(value) {
                                // Formatter en GB/MB/KB
                                if (value >= 1073741824) {
                                    return (value / 1073741824).toFixed(1) + ' GB';
                                } else if (value >= 1048576) {
                                    return (value / 1048576).toFixed(1) + ' MB';
                                } else if (value >= 1024) {
                                    return (value / 1024).toFixed(1) + ' KB';
                                }
                                return value + ' B';
                            }
                        },
                        grid: {
                            color: 'rgba(100, 116, 139, 0.1)',
                            drawBorder: false
                        }
                    }
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                }
            }
        });

        // Initialiser le sélecteur d'instance
        this.initNetworkInstanceSelector(networkData.instances);
    }

    /**
     * Initialise le sélecteur d'instance pour le graphique réseau
     */
    initNetworkInstanceSelector(instances) {
        const selector = document.getElementById('network-instance-selector');
        if (!selector) return;

        // Vider et remplir le sélecteur
        selector.innerHTML = '<option value="all">All Instances (Top 10)</option>';
        instances.forEach((instance, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = instance.name;
            selector.appendChild(option);
        });

        // Event listener pour le changement de sélection
        selector.addEventListener('change', (e) => {
            const selectedValue = e.target.value;
            const chart = this.charts.network;
            const networkData = ec2Stats.getNetworkByInstance();

            if (selectedValue === 'all') {
                // Afficher toutes les instances (Top 10)
                chart.data.labels = networkData.labels;
                chart.data.datasets[0].data = networkData.dataIn;
                chart.data.datasets[1].data = networkData.dataOut;

                // Style normal avec opacité réduite
                chart.data.datasets[0].backgroundColor = 'rgba(6, 182, 212, 0.5)';
                chart.data.datasets[0].borderColor = '#06b6d4';
                chart.data.datasets[1].backgroundColor = 'rgba(139, 92, 246, 0.5)';
                chart.data.datasets[1].borderColor = '#8b5cf6';

            } else {
                // Afficher uniquement l'instance sélectionnée
                const selectedIndex = parseInt(selectedValue);
                const selectedInstance = instances[selectedIndex];

                chart.data.labels = [selectedInstance.name];
                chart.data.datasets[0].data = [selectedInstance.networkIn];
                chart.data.datasets[1].data = [selectedInstance.networkOut];

                // Style brillant pour l'instance sélectionnée
                chart.data.datasets[0].backgroundColor = 'rgba(6, 182, 212, 0.9)';
                chart.data.datasets[0].borderColor = '#06b6d4';
                chart.data.datasets[0].borderWidth = 3;
                chart.data.datasets[1].backgroundColor = 'rgba(139, 92, 246, 0.9)';
                chart.data.datasets[1].borderColor = '#8b5cf6';
                chart.data.datasets[1].borderWidth = 3;
            }

            chart.update('active'); // Update avec animation
        });

        // Ajouter l'effet de sur-brillance au hover sur les barres
        const canvas = document.getElementById('chart-network-instances');
        if (canvas) {
            let lastHoveredIndex = -1;

            canvas.addEventListener('mousemove', (e) => {
                const chart = this.charts.network;
                const activeElements = chart.getElementsAtEventForMode(e, 'index', { intersect: false }, false);

                if (activeElements.length > 0 && selector.value === 'all') {
                    const hoveredIndex = activeElements[0].index;

                    // Éviter les updates inutiles
                    if (hoveredIndex !== lastHoveredIndex) {
                        lastHoveredIndex = hoveredIndex;

                        // Appliquer l'effet de sur-brillance sur l'instance survolée
                        const networkData = ec2Stats.getNetworkByInstance();

                        chart.data.datasets[0].backgroundColor = networkData.labels.map((_, i) =>
                            i === hoveredIndex ? 'rgba(6, 182, 212, 0.95)' : 'rgba(6, 182, 212, 0.3)'
                        );
                        chart.data.datasets[1].backgroundColor = networkData.labels.map((_, i) =>
                            i === hoveredIndex ? 'rgba(139, 92, 246, 0.95)' : 'rgba(139, 92, 246, 0.3)'
                        );

                        chart.update('none');
                    }
                }
            });

            canvas.addEventListener('mouseleave', () => {
                lastHoveredIndex = -1;
                // Restaurer l'état initial quand la souris quitte le canvas
                if (selector.value === 'all') {
                    const chart = this.charts.network;
                    chart.data.datasets[0].backgroundColor = 'rgba(6, 182, 212, 0.5)';
                    chart.data.datasets[1].backgroundColor = 'rgba(139, 92, 246, 0.5)';
                    chart.update('none');
                }
            });
        }

        // Déclencher l'état initial (all instances)
        selector.value = 'all';
        selector.dispatchEvent(new Event('change'));
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
        this.populateRegionFilter();
        this.renderInstancesTable();
    }

    /**
     * Remplit le filtre de régions avec les régions disponibles
     */
    populateRegionFilter() {
        const filterRegion = document.getElementById('filter-region');
        if (!filterRegion) return;

        // Récupérer toutes les régions uniques
        const regions = [...new Set(ec2Stats.instances.map(i => i.region))].sort();

        // Vider le select (garder seulement "Toutes les régions")
        filterRegion.innerHTML = '<option value="all">Toutes les régions</option>';

        // Ajouter chaque région
        regions.forEach(region => {
            const option = document.createElement('option');
            option.value = region;
            option.textContent = region;
            filterRegion.appendChild(option);
        });

        console.log(`✅ Filtre régions rempli avec ${regions.length} régions:`, regions);
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

        // Filtre par région
        document.getElementById('filter-region').addEventListener('change', (e) => this.filterByRegion(e.target.value));

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
     * Filtre par région
     */
    filterByRegion(region) {
        if (region === 'all') {
            this.filteredInstances = ec2Stats.instances;
        } else {
            this.filteredInstances = ec2Stats.instances.filter(i => i.region === region);
        }
        this.renderInstancesTable();
        console.log(`🔍 Filtré par région: ${region} (${this.filteredInstances.length} instances)`);
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

