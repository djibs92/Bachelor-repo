/**
 * Dashboard RDS - Gestion de l'affichage et des graphiques
 */

class DashboardRDS {
    constructor() {
        this.rdsStats = new RDSStats();
        this.charts = {};
        this.currentRegionFilter = 'all';
        this.filteredInstances = [];
    }

    /**
     * Initialise le dashboard
     */
    async init() {
        try {
            console.log('🚀 Initialisation du dashboard RDS...');

            // Afficher le loader
            this.showLoader();

            // Charger les données
            console.log('📡 Chargement des instances RDS depuis l\'API...');
            await this.rdsStats.loadInstances({ limit: 100 });
            console.log(`✅ ${this.rdsStats.instances.length} instances RDS chargées`);

            // Masquer le loader
            this.hideLoader();

            // Vérifier s'il y a des données
            if (this.rdsStats.instances.length === 0) {
                console.warn('⚠️ Aucune instance RDS trouvée');
                this.showNoDataMessage();
                return;
            }

            // Initialiser les instances filtrées
            this.filteredInstances = this.rdsStats.instances;

            // Mettre à jour l'interface
            this.displayStats();
            this.displayAlerts();
            this.createCharts();
            this.displayInstancesTable();
            this.initializeFilters();

            console.log('✅ Dashboard RDS chargé avec succès');
        } catch (error) {
            console.error('❌ Erreur initialisation dashboard RDS:', error);
            this.hideLoader();
            this.showError('Erreur lors du chargement du dashboard RDS');
        }
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
     * Affiche un message quand il n'y a pas de données
     */
    showNoDataMessage() {
        const container = document.querySelector('main .container');
        if (container) {
            container.innerHTML = `
                <div class="glass-card p-8 text-center">
                    <span class="material-symbols-outlined text-6xl text-slate-600 mb-4">database</span>
                    <h3 class="text-xl font-semibold text-white mb-2">Aucune instance RDS trouvée</h3>
                    <p class="text-slate-400 mb-6">Lancez un scan RDS pour commencer à analyser vos bases de données.</p>
                    <a href="config-scan-new.html" class="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/80 transition-colors">
                        <span class="material-symbols-outlined">radar</span>
                        Lancer un scan
                    </a>
                </div>
            `;
        }
    }

    /**
     * Affiche un message d'erreur
     */
    showError(message) {
        const container = document.querySelector('main .container');
        if (container) {
            container.innerHTML = `
                <div class="glass-card p-8 text-center">
                    <span class="material-symbols-outlined text-6xl text-red-500 mb-4">error</span>
                    <h3 class="text-xl font-semibold text-white mb-2">Erreur</h3>
                    <p class="text-slate-400">${message}</p>
                </div>
            `;
        }
    }

    /**
     * Affiche les statistiques dans les cartes
     */
    displayStats() {
        const totalStats = this.rdsStats.getTotalInstancesStats();
        const securityStats = this.rdsStats.getSecurityStats();
        const storageStats = this.rdsStats.getStorageStats();
        const regions = this.rdsStats.getActiveRegions();

        // Carte 1: Total Instances
        document.getElementById('total-instances').textContent = totalStats.total;
        document.getElementById('instances-detail').textContent = `${totalStats.running} actives`;

        // Carte 2: Régions actives
        document.getElementById('active-regions').textContent = regions.length;
        document.getElementById('regions-detail').textContent = regions.join(', ') || 'Aucune région';

        // Carte 3: Stockage total
        document.getElementById('total-storage').textContent = `${storageStats.totalStorage} GB`;
        const encryptedCount = securityStats.encrypted;
        document.getElementById('storage-detail').textContent = `${encryptedCount} chiffré(s)`;

        // Carte 4: Score de sécurité
        const scoreEl = document.getElementById('security-score');
        scoreEl.textContent = `${securityStats.securityScore}%`;
        scoreEl.className = `stat-value ${this.getSecurityScoreColor(securityStats.securityScore)}`;
        document.getElementById('security-detail').textContent = `${securityStats.encrypted}/${totalStats.total} chiffrés`;
    }

    /**
     * Retourne la couleur selon le score de sécurité
     */
    getSecurityScoreColor(score) {
        if (score >= 80) return 'text-success';
        if (score >= 50) return 'text-warning';
        return 'text-danger';
    }

    /**
     * Affiche les alertes
     */
    displayAlerts() {
        const alerts = this.rdsStats.generateAlerts();
        const alertsSection = document.getElementById('alerts-section');
        const alertsContainer = document.getElementById('alerts-container');

        if (!alertsSection || !alertsContainer) return;

        if (alerts.length === 0) {
            alertsSection.classList.add('hidden');
            return;
        }

        alertsSection.classList.remove('hidden');
        alertsContainer.innerHTML = alerts.map(alert => `
            <div class="glass-card p-4 border-l-4 ${this.getAlertBorderColor(alert.type)}">
                <div class="flex items-start gap-3">
                    <span class="material-symbols-outlined ${this.getAlertIconColor(alert.type)}">${alert.icon}</span>
                    <div class="flex-1">
                        <h4 class="text-white font-semibold mb-1">${alert.title}</h4>
                        <p class="text-slate-400 text-sm">${alert.message}</p>
                    </div>
                </div>
            </div>
        `).join('');
    }

    /**
     * Retourne la couleur de bordure selon le type d'alerte
     */
    getAlertBorderColor(type) {
        switch (type) {
            case 'danger': return 'border-danger';
            case 'warning': return 'border-warning';
            case 'info': return 'border-accent';
            default: return 'border-slate-600';
        }
    }

    /**
     * Retourne la couleur d'icône selon le type d'alerte
     */
    getAlertIconColor(type) {
        switch (type) {
            case 'danger': return 'text-danger';
            case 'warning': return 'text-warning';
            case 'info': return 'text-accent';
            default: return 'text-slate-400';
        }
    }

    /**
     * Crée les graphiques
     */
    createCharts() {
        this.createEngineDistributionChart();
        this.createCPUChart();
        this.createIOPSChart();
        this.createLatencyChart();
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
     * Retourne la couleur en fonction des IOPS (cyan gradient)
     */
    getIOPSColor(iopsValue, maxIops) {
        const ratio = Math.min(iopsValue / maxIops, 1);
        // Cyan clair → Cyan foncé
        return `rgba(${Math.round(6 + ratio * 0)}, ${Math.round(182 + ratio * 0)}, ${Math.round(212 - ratio * 50)}, ${0.6 + ratio * 0.3})`;
    }

    /**
     * Retourne la couleur en fonction de la latence (plus c'est élevé, plus c'est rouge)
     */
    getLatencyColor(latencyMs) {
        if (latencyMs < 5) {
            // Vert (latence faible)
            return 'rgba(34, 197, 94, 0.8)';
        } else if (latencyMs < 10) {
            // Jaune
            const ratio = (latencyMs - 5) / 5;
            return `rgba(${Math.round(34 + ratio * 200)}, ${Math.round(197 + ratio * 22)}, ${Math.round(94 - ratio * 86)}, 0.8)`;
        } else if (latencyMs < 20) {
            // Orange
            const ratio = (latencyMs - 10) / 10;
            return `rgba(${Math.round(234 + ratio * 17)}, ${Math.round(179 - ratio * 64)}, ${Math.round(8 + ratio * 2)}, 0.8)`;
        } else {
            // Rouge (latence élevée)
            return 'rgba(239, 68, 68, 0.9)';
        }
    }

    /**
     * Graphique: Distribution par moteur de base de données (Donut moderne)
     */
    createEngineDistributionChart() {
        const ctx = document.getElementById('engine-distribution-chart');
        if (!ctx) return;

        const engineStats = this.rdsStats.getEngineStats();
        const labels = Object.keys(engineStats);
        const data = Object.values(engineStats);

        // Couleurs pour chaque moteur
        const colors = {
            'postgres': '#336791',
            'mysql': '#4479A1',
            'mariadb': '#003545',
            'oracle': '#F80000',
            'sqlserver': '#CC2927',
            'aurora': '#FF9900',
            'aurora-mysql': '#FF9900',
            'aurora-postgresql': '#336791'
        };

        const backgroundColors = labels.map(engine => colors[engine] || '#8B5CF6');

        if (this.charts.engineChart) {
            this.charts.engineChart.destroy();
        }

        this.charts.engineChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.map(l => l.toUpperCase()),
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors,
                    borderWidth: 0,
                    hoverBorderWidth: 0,
                    hoverOffset: 15,
                    spacing: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '65%',
                layout: {
                    padding: 20
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.98)',
                        titleColor: '#06b6d4',
                        bodyColor: '#e2e8f0',
                        borderColor: '#06b6d4',
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
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                }
            }
        });
    }

    /**
     * Graphique: CPU Utilization (Bar moderne style EC2 avec couleurs dynamiques)
     */
    createCPUChart() {
        const ctx = document.getElementById('cpu-chart');
        if (!ctx) return;

        // Récupérer les instances avec leurs CPU
        const instances = this.rdsStats.instances
            .filter(i => i.performance?.cpu_utilization_avg != null)
            .sort((a, b) => (b.performance?.cpu_utilization_avg || 0) - (a.performance?.cpu_utilization_avg || 0))
            .slice(0, 10); // Top 10

        // Stocker les données pour le sélecteur
        this.cpuInstancesData = instances.map((i, index) => ({
            index: index,
            name: i.db_instance_identifier || i.instance_id,
            cpu: i.performance?.cpu_utilization_avg || 0
        }));

        const labels = instances.map(i => i.db_instance_identifier || i.instance_id);
        const cpuData = instances.map(i => i.performance?.cpu_utilization_avg || 0);

        // Créer les couleurs dynamiques basées sur l'utilisation CPU
        const backgroundColors = cpuData.map(cpu => this.getCPUColor(cpu));
        const borderColors = cpuData.map(cpu => {
            const color = this.getCPUColor(cpu);
            return color.replace('0.8', '1').replace('0.9', '1');
        });

        if (this.charts.cpuChart) {
            this.charts.cpuChart.destroy();
        }

        // Calculer le max dynamique pour mieux visualiser les petites valeurs
        const maxCpu = Math.max(...cpuData, 10); // Minimum 10% pour la visibilité
        const suggestedMax = maxCpu < 5 ? 5 : (maxCpu < 20 ? 20 : (maxCpu < 50 ? 50 : 100));

        this.charts.cpuChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'CPU %',
                    data: cpuData,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                    barThickness: 24,
                    minBarLength: 3  // Longueur minimale pour voir les petites valeurs
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.98)',
                        titleColor: '#06b6d4',
                        bodyColor: '#e2e8f0',
                        borderColor: '#06b6d4',
                        borderWidth: 1,
                        padding: 12,
                        titleFont: { size: 13, family: 'Rajdhani', weight: '600' },
                        bodyFont: { size: 12, family: 'Rajdhani', weight: '500' },
                        callbacks: {
                            label: (context) => ` CPU: ${context.parsed.x.toFixed(2)}%`
                        }
                    },
                    // Plugin pour afficher les valeurs à côté des barres
                    datalabels: false
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: suggestedMax,
                        ticks: {
                            color: '#94a3b8',
                            font: { size: 11, family: 'Rajdhani' },
                            callback: (value) => value + '%'
                        },
                        grid: {
                            color: 'rgba(51, 65, 85, 0.3)',
                            drawBorder: false
                        },
                        title: {
                            display: true,
                            text: suggestedMax < 100 ? `Scale: 0-${suggestedMax}% (optimized for low values)` : '',
                            color: '#64748b',
                            font: { size: 10, family: 'Rajdhani', style: 'italic' }
                        }
                    },
                    y: {
                        ticks: {
                            color: '#94a3b8',
                            font: { size: 10, family: 'Rajdhani' },
                            autoSkip: false
                        },
                        grid: { display: false }
                    }
                },
                // Ajouter les valeurs à la fin des barres
                animation: {
                    onComplete: () => {
                        const chartInstance = this.charts.cpuChart;
                        const ctx = chartInstance.ctx;

                        ctx.font = 'bold 11px Rajdhani';
                        ctx.textAlign = 'left';
                        ctx.textBaseline = 'middle';

                        chartInstance.data.datasets.forEach((dataset, i) => {
                            const meta = chartInstance.getDatasetMeta(i);
                            meta.data.forEach((bar, index) => {
                                const data = dataset.data[index];
                                const x = bar.x + 5;
                                const y = bar.y;

                                // Couleur du texte selon la valeur
                                if (data < 1) {
                                    ctx.fillStyle = '#22c55e'; // Vert
                                } else if (data < 50) {
                                    ctx.fillStyle = '#eab308'; // Jaune
                                } else if (data < 75) {
                                    ctx.fillStyle = '#f97316'; // Orange
                                } else {
                                    ctx.fillStyle = '#ef4444'; // Rouge
                                }

                                ctx.fillText(data.toFixed(2) + '%', x, y);
                            });
                        });
                    }
                }
            }
        });

        // Ajouter le sélecteur d'instance
        const selector = document.getElementById('cpu-instance-selector');
        if (selector) {
            // Remplir le sélecteur avec les instances
            selector.innerHTML = '<option value="all">All Databases</option>';
            this.cpuInstancesData.forEach((instance, index) => {
                const option = document.createElement('option');
                option.value = index;
                // Afficher 2 décimales pour les petites valeurs, 1 pour les grandes
                const cpuDisplay = instance.cpu < 10 ? instance.cpu.toFixed(2) : instance.cpu.toFixed(1);
                option.textContent = `${instance.name} (${cpuDisplay}%)`;
                selector.appendChild(option);
            });

            // Gérer le changement de sélection
            selector.addEventListener('change', (e) => {
                const selectedValue = e.target.value;
                const chart = this.charts.cpuChart;

                if (selectedValue === 'all') {
                    // Afficher toutes les instances (Top 10)
                    const instances = this.cpuInstancesData;
                    chart.data.labels = instances.map(i => i.name);
                    chart.data.datasets[0].data = instances.map(i => i.cpu);

                    // Recréer les couleurs dynamiques
                    chart.data.datasets[0].backgroundColor = instances.map(i => this.getCPUColor(i.cpu));
                    chart.data.datasets[0].borderColor = instances.map(i => {
                        const color = this.getCPUColor(i.cpu);
                        return color.replace('0.8', '1').replace('0.9', '1');
                    });
                    chart.data.datasets[0].barThickness = 20;
                } else {
                    // Afficher uniquement l'instance sélectionnée
                    const selectedIndex = parseInt(selectedValue);
                    const selectedInstance = this.cpuInstancesData[selectedIndex];

                    chart.data.labels = [selectedInstance.name];
                    chart.data.datasets[0].data = [selectedInstance.cpu];

                    // Couleur brillante pour l'instance sélectionnée
                    const color = this.getCPUColor(selectedInstance.cpu);
                    chart.data.datasets[0].backgroundColor = [color.replace('0.8', '0.95').replace('0.9', '0.95')];
                    chart.data.datasets[0].borderColor = [color.replace('0.8', '1').replace('0.9', '1')];
                    chart.data.datasets[0].borderWidth = 3;
                    chart.data.datasets[0].barThickness = 40;
                }

                chart.update('active');
            });

            // Ajouter l'effet de sur-brillance au hover
            const canvas = document.getElementById('cpu-chart');
            if (canvas) {
                let lastHoveredIndex = -1;

                canvas.addEventListener('mousemove', (e) => {
                    const chart = this.charts.cpuChart;
                    const activeElements = chart.getElementsAtEventForMode(e, 'index', { intersect: false }, false);

                    if (activeElements.length > 0 && selector.value === 'all') {
                        const hoveredIndex = activeElements[0].index;

                        if (hoveredIndex !== lastHoveredIndex) {
                            lastHoveredIndex = hoveredIndex;

                            // Appliquer l'effet de sur-brillance sur l'instance survolée
                            const instances = this.cpuInstancesData;

                            chart.data.datasets[0].backgroundColor = instances.map((i, idx) => {
                                const color = this.getCPUColor(i.cpu);
                                return idx === hoveredIndex
                                    ? color.replace('0.8', '0.95').replace('0.9', '0.95')
                                    : color.replace('0.8', '0.4').replace('0.9', '0.4');
                            });

                            chart.data.datasets[0].borderWidth = instances.map((_, idx) =>
                                idx === hoveredIndex ? 3 : 2
                            );

                            chart.update('none');
                        }
                    }
                });

                canvas.addEventListener('mouseleave', () => {
                    lastHoveredIndex = -1;
                    // Restaurer l'état initial quand la souris quitte le canvas
                    if (selector.value === 'all') {
                        const instances = this.cpuInstancesData;
                        this.charts.cpuChart.data.datasets[0].backgroundColor = instances.map(i => this.getCPUColor(i.cpu));
                        this.charts.cpuChart.data.datasets[0].borderWidth = 2;
                        this.charts.cpuChart.update('none');
                    }
                });
            }

            // Déclencher l'état initial (all instances)
            selector.value = 'all';
            selector.dispatchEvent(new Event('change'));
        }
    }

    /**
     * Graphique: IOPS (Read + Write)
     */
    createIOPSChart() {
        const ctx = document.getElementById('iops-chart');
        if (!ctx) return;

        // Récupérer les instances avec IOPS
        const instances = this.rdsStats.instances
            .filter(i => i.performance?.read_iops_avg != null || i.performance?.write_iops_avg != null)
            .sort((a, b) => {
                const totalA = (a.performance?.read_iops_avg || 0) + (a.performance?.write_iops_avg || 0);
                const totalB = (b.performance?.read_iops_avg || 0) + (b.performance?.write_iops_avg || 0);
                return totalB - totalA;
            })
            .slice(0, 8); // Top 8

        // Stocker les données pour le sélecteur
        this.iopsInstancesData = instances.map((i, index) => ({
            index: index,
            name: i.db_instance_identifier || i.instance_id,
            read: i.performance?.read_iops_avg || 0,
            write: i.performance?.write_iops_avg || 0
        }));

        const labels = instances.map(i => i.db_instance_identifier || i.instance_id);
        const readData = instances.map(i => i.performance?.read_iops_avg || 0);
        const writeData = instances.map(i => i.performance?.write_iops_avg || 0);

        // Calculer le max dynamique pour mieux visualiser les petites valeurs
        const maxIOPS = Math.max(...readData, ...writeData, 5);
        const suggestedMaxIOPS = maxIOPS < 10 ? 10 : (maxIOPS < 50 ? 50 : (maxIOPS < 100 ? 100 : Math.ceil(maxIOPS / 100) * 100));

        if (this.charts.iopsChart) {
            this.charts.iopsChart.destroy();
        }

        // Créer des gradients pour les barres
        const chartCanvas = ctx.getContext('2d');

        // Gradient bleu pour Read IOPS (bleu clair → bleu foncé)
        const readGradient = chartCanvas.createLinearGradient(0, 0, 0, 400);
        readGradient.addColorStop(0, 'rgba(96, 165, 250, 0.9)');    // Bleu clair
        readGradient.addColorStop(0.5, 'rgba(59, 130, 246, 0.85)'); // Bleu moyen
        readGradient.addColorStop(1, 'rgba(37, 99, 235, 0.8)');     // Bleu foncé

        // Gradient vert pour Write IOPS (vert clair → vert foncé)
        const writeGradient = chartCanvas.createLinearGradient(0, 0, 0, 400);
        writeGradient.addColorStop(0, 'rgba(52, 211, 153, 0.9)');   // Vert clair
        writeGradient.addColorStop(0.5, 'rgba(16, 185, 129, 0.85)'); // Vert moyen
        writeGradient.addColorStop(1, 'rgba(5, 150, 105, 0.8)');    // Vert foncé

        this.charts.iopsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Read IOPS',
                    data: readData,
                    backgroundColor: readGradient,
                    borderColor: 'rgba(96, 165, 250, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                    barThickness: 18,
                    minBarLength: 3
                }, {
                    label: 'Write IOPS',
                    data: writeData,
                    backgroundColor: writeGradient,
                    borderColor: 'rgba(52, 211, 153, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                    barThickness: 18,
                    minBarLength: 3
                }]
            },
            options: {
                indexAxis: 'y',  // ✅ Barres horizontales
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
                        labels: {
                            color: '#e2e8f0',
                            font: { size: 12, family: 'Rajdhani', weight: '700' },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'rectRounded',
                            boxWidth: 12,
                            boxHeight: 12
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.98)',
                        titleColor: '#06b6d4',
                        bodyColor: '#e2e8f0',
                        borderColor: '#06b6d4',
                        borderWidth: 2,
                        padding: 14,
                        titleFont: { size: 14, family: 'Rajdhani', weight: '700' },
                        bodyFont: { size: 13, family: 'Rajdhani', weight: '600' },
                        displayColors: true,
                        boxWidth: 10,
                        boxHeight: 10,
                        boxPadding: 6,
                        callbacks: {
                            label: (context) => ` ${context.dataset.label}: ${context.parsed.x.toFixed(1)} IOPS`
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: suggestedMaxIOPS,
                        ticks: {
                            color: '#94a3b8',
                            font: { size: 11, family: 'Rajdhani', weight: '600' },
                            callback: (value) => value.toFixed(0)
                        },
                        grid: {
                            color: 'rgba(51, 65, 85, 0.3)',
                            drawBorder: false,
                            lineWidth: 1
                        },
                        title: {
                            display: true,
                            text: suggestedMaxIOPS < 100 ? `IOPS (scale: 0-${suggestedMaxIOPS})` : 'IOPS',
                            color: '#64748b',
                            font: { size: 11, family: 'Rajdhani', weight: '700' }
                        }
                    },
                    y: {
                        ticks: {
                            color: '#94a3b8',
                            font: { size: 10, family: 'Rajdhani', weight: '600' },
                            autoSkip: false
                        },
                        grid: {
                            display: false,
                            drawBorder: false
                        }
                    }
                }
            }
        });

        // Ajouter le sélecteur d'instance pour IOPS
        const selector = document.getElementById('iops-instance-selector');
        if (selector) {
            // Remplir le sélecteur avec les instances
            selector.innerHTML = '<option value="all">All Databases</option>';
            this.iopsInstancesData.forEach((instance, index) => {
                const option = document.createElement('option');
                option.value = index;
                const total = instance.read + instance.write;
                option.textContent = `${instance.name} (${total.toFixed(0)} IOPS)`;
                selector.appendChild(option);
            });

            // Gérer le changement de sélection
            selector.addEventListener('change', (e) => {
                const selectedValue = e.target.value;
                const chart = this.charts.iopsChart;

                if (selectedValue === 'all') {
                    // Afficher toutes les instances (Top 8)
                    const instances = this.iopsInstancesData;
                    chart.data.labels = instances.map(i => i.name);
                    chart.data.datasets[0].data = instances.map(i => i.read);
                    chart.data.datasets[1].data = instances.map(i => i.write);
                    chart.data.datasets[0].barThickness = 18;
                    chart.data.datasets[1].barThickness = 18;
                } else {
                    // Afficher uniquement l'instance sélectionnée
                    const selectedIndex = parseInt(selectedValue);
                    const selectedInstance = this.iopsInstancesData[selectedIndex];

                    chart.data.labels = [selectedInstance.name];
                    chart.data.datasets[0].data = [selectedInstance.read];
                    chart.data.datasets[1].data = [selectedInstance.write];
                    chart.data.datasets[0].barThickness = 40;
                    chart.data.datasets[1].barThickness = 40;
                }

                chart.update('active');
            });

            // Déclencher l'état initial (all instances)
            selector.value = 'all';
            selector.dispatchEvent(new Event('change'));

            // Ajouter l'effet de sur-brillance au hover
            const canvas = document.getElementById('iops-chart');
            if (canvas) {
                let lastHoveredIndex = -1;

                canvas.addEventListener('mousemove', (e) => {
                    const chart = this.charts.iopsChart;
                    const activeElements = chart.getElementsAtEventForMode(e, 'index', { intersect: false }, false);

                    if (activeElements.length > 0 && selector.value === 'all') {
                        const hoveredIndex = activeElements[0].index;

                        if (hoveredIndex !== lastHoveredIndex) {
                            lastHoveredIndex = hoveredIndex;

                            // Créer les gradients à nouveau
                            const ctx = canvas.getContext('2d');
                            const readGradient = ctx.createLinearGradient(0, 0, 0, 400);
                            const writeGradient = ctx.createLinearGradient(0, 0, 0, 400);

                            // Appliquer l'effet de surbrillance
                            chart.data.datasets[0].backgroundColor = this.iopsInstancesData.map((_, idx) => {
                                if (idx === hoveredIndex) {
                                    // Barre surbrillante (Read)
                                    readGradient.addColorStop(0, 'rgba(96, 165, 250, 1)');
                                    readGradient.addColorStop(0.5, 'rgba(59, 130, 246, 0.95)');
                                    readGradient.addColorStop(1, 'rgba(37, 99, 235, 0.9)');
                                    return readGradient;
                                } else {
                                    // Barre atténuée (Read)
                                    return 'rgba(59, 130, 246, 0.3)';
                                }
                            });

                            chart.data.datasets[1].backgroundColor = this.iopsInstancesData.map((_, idx) => {
                                if (idx === hoveredIndex) {
                                    // Barre surbrillante (Write)
                                    writeGradient.addColorStop(0, 'rgba(52, 211, 153, 1)');
                                    writeGradient.addColorStop(0.5, 'rgba(16, 185, 129, 0.95)');
                                    writeGradient.addColorStop(1, 'rgba(5, 150, 105, 0.9)');
                                    return writeGradient;
                                } else {
                                    // Barre atténuée (Write)
                                    return 'rgba(16, 185, 129, 0.3)';
                                }
                            });

                            chart.data.datasets[0].borderWidth = this.iopsInstancesData.map((_, idx) => idx === hoveredIndex ? 3 : 2);
                            chart.data.datasets[1].borderWidth = this.iopsInstancesData.map((_, idx) => idx === hoveredIndex ? 3 : 2);

                            chart.update('none');
                        }
                    }
                });

                canvas.addEventListener('mouseleave', () => {
                    if (selector.value === 'all') {
                        lastHoveredIndex = -1;
                        const chart = this.charts.iopsChart;
                        const ctx = canvas.getContext('2d');

                        // Restaurer les gradients normaux
                        const readGradient = ctx.createLinearGradient(0, 0, 0, 400);
                        readGradient.addColorStop(0, 'rgba(96, 165, 250, 0.9)');
                        readGradient.addColorStop(0.5, 'rgba(59, 130, 246, 0.85)');
                        readGradient.addColorStop(1, 'rgba(37, 99, 235, 0.8)');

                        const writeGradient = ctx.createLinearGradient(0, 0, 0, 400);
                        writeGradient.addColorStop(0, 'rgba(52, 211, 153, 0.9)');
                        writeGradient.addColorStop(0.5, 'rgba(16, 185, 129, 0.85)');
                        writeGradient.addColorStop(1, 'rgba(5, 150, 105, 0.8)');

                        chart.data.datasets[0].backgroundColor = readGradient;
                        chart.data.datasets[1].backgroundColor = writeGradient;
                        chart.data.datasets[0].borderWidth = 2;
                        chart.data.datasets[1].borderWidth = 2;

                        chart.update('none');
                    }
                });
            }
        }
    }

    /**
     * Graphique: Latence (Read + Write)
     */
    createLatencyChart() {
        const ctx = document.getElementById('latency-chart');
        if (!ctx) return;

        // Récupérer les instances avec latence
        const instances = this.rdsStats.instances
            .filter(i => i.performance?.read_latency_avg != null || i.performance?.write_latency_avg != null)
            .sort((a, b) => {
                const totalA = (a.performance?.read_latency_avg || 0) + (a.performance?.write_latency_avg || 0);
                const totalB = (b.performance?.read_latency_avg || 0) + (b.performance?.write_latency_avg || 0);
                return totalB - totalA;
            })
            .slice(0, 8); // Top 8

        // Stocker les données pour le sélecteur
        this.latencyInstancesData = instances.map((i, index) => ({
            index: index,
            name: i.db_instance_identifier || i.instance_id,
            read: (i.performance?.read_latency_avg || 0) * 1000,
            write: (i.performance?.write_latency_avg || 0) * 1000
        }));

        const labels = instances.map(i => i.db_instance_identifier || i.instance_id);
        const readData = instances.map(i => (i.performance?.read_latency_avg || 0) * 1000); // Convertir en ms
        const writeData = instances.map(i => (i.performance?.write_latency_avg || 0) * 1000); // Convertir en ms

        // Calculer le max dynamique pour mieux visualiser les petites valeurs
        const maxLatency = Math.max(...readData, ...writeData, 1);
        const suggestedMaxLatency = maxLatency < 2 ? 2 : (maxLatency < 5 ? 5 : (maxLatency < 10 ? 10 : (maxLatency < 50 ? 50 : Math.ceil(maxLatency / 10) * 10)));

        if (this.charts.latencyChart) {
            this.charts.latencyChart.destroy();
        }

        // Créer des gradients pour les barres
        const chartCanvas = ctx.getContext('2d');

        // Gradient orange pour Read Latency (orange clair → orange foncé)
        const readLatencyGradient = chartCanvas.createLinearGradient(0, 0, 0, 400);
        readLatencyGradient.addColorStop(0, 'rgba(251, 146, 60, 0.95)');   // Orange clair
        readLatencyGradient.addColorStop(0.5, 'rgba(249, 115, 22, 0.9)');  // Orange moyen
        readLatencyGradient.addColorStop(1, 'rgba(234, 88, 12, 0.85)');    // Orange foncé

        // Gradient violet pour Write Latency (violet clair → violet foncé)
        const writeLatencyGradient = chartCanvas.createLinearGradient(0, 0, 0, 400);
        writeLatencyGradient.addColorStop(0, 'rgba(167, 139, 250, 0.95)');  // Violet clair
        writeLatencyGradient.addColorStop(0.5, 'rgba(139, 92, 246, 0.9)');  // Violet moyen
        writeLatencyGradient.addColorStop(1, 'rgba(124, 58, 237, 0.85)');   // Violet foncé

        this.charts.latencyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Read Latency',
                    data: readData,
                    backgroundColor: readLatencyGradient,
                    borderColor: 'rgba(251, 146, 60, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                    barThickness: 18,
                    minBarLength: 3
                }, {
                    label: 'Write Latency',
                    data: writeData,
                    backgroundColor: writeLatencyGradient,
                    borderColor: 'rgba(167, 139, 250, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                    barThickness: 18,
                    minBarLength: 3
                }]
            },
            options: {
                indexAxis: 'y',  // ✅ Barres horizontales
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
                        labels: {
                            color: '#e2e8f0',
                            font: { size: 12, family: 'Rajdhani', weight: '700' },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'rectRounded',
                            boxWidth: 12,
                            boxHeight: 12
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.98)',
                        titleColor: '#06b6d4',
                        bodyColor: '#e2e8f0',
                        borderColor: '#06b6d4',
                        borderWidth: 2,
                        padding: 14,
                        titleFont: { size: 14, family: 'Rajdhani', weight: '700' },
                        bodyFont: { size: 13, family: 'Rajdhani', weight: '600' },
                        displayColors: true,
                        boxWidth: 10,
                        boxHeight: 10,
                        boxPadding: 6,
                        callbacks: {
                            label: (context) => ` ${context.dataset.label}: ${context.parsed.x.toFixed(2)} ms`
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: suggestedMaxLatency,
                        ticks: {
                            color: '#94a3b8',
                            font: { size: 11, family: 'Rajdhani', weight: '600' },
                            callback: (value) => value.toFixed(1) + ' ms'
                        },
                        grid: {
                            color: 'rgba(51, 65, 85, 0.3)',
                            drawBorder: false,
                            lineWidth: 1
                        },
                        title: {
                            display: true,
                            text: suggestedMaxLatency < 10 ? `Latency (scale: 0-${suggestedMaxLatency} ms)` : 'Latency (ms)',
                            color: '#64748b',
                            font: { size: 11, family: 'Rajdhani', weight: '700' }
                        }
                    },
                    y: {
                        ticks: {
                            color: '#94a3b8',
                            font: { size: 10, family: 'Rajdhani', weight: '600' },
                            autoSkip: false
                        },
                        grid: {
                            display: false,
                            drawBorder: false
                        }
                    }
                }
            }
        });

        // Ajouter le sélecteur d'instance pour Latence
        const selector = document.getElementById('latency-instance-selector');
        if (selector) {
            // Remplir le sélecteur avec les instances
            selector.innerHTML = '<option value="all">All Databases</option>';
            this.latencyInstancesData.forEach((instance, index) => {
                const option = document.createElement('option');
                option.value = index;
                const avgLatency = (instance.read + instance.write) / 2;
                option.textContent = `${instance.name} (${avgLatency.toFixed(2)} ms)`;
                selector.appendChild(option);
            });

            // Gérer le changement de sélection
            selector.addEventListener('change', (e) => {
                const selectedValue = e.target.value;
                const chart = this.charts.latencyChart;

                if (selectedValue === 'all') {
                    // Afficher toutes les instances (Top 8)
                    const instances = this.latencyInstancesData;
                    chart.data.labels = instances.map(i => i.name);
                    chart.data.datasets[0].data = instances.map(i => i.read);
                    chart.data.datasets[1].data = instances.map(i => i.write);
                    chart.data.datasets[0].barThickness = 18;
                    chart.data.datasets[1].barThickness = 18;
                } else {
                    // Afficher uniquement l'instance sélectionnée
                    const selectedIndex = parseInt(selectedValue);
                    const selectedInstance = this.latencyInstancesData[selectedIndex];

                    chart.data.labels = [selectedInstance.name];
                    chart.data.datasets[0].data = [selectedInstance.read];
                    chart.data.datasets[1].data = [selectedInstance.write];
                    chart.data.datasets[0].barThickness = 40;
                    chart.data.datasets[1].barThickness = 40;
                }

                chart.update('active');
            });

            // Déclencher l'état initial (all instances)
            selector.value = 'all';
            selector.dispatchEvent(new Event('change'));

            // Ajouter l'effet de sur-brillance au hover
            const canvas = document.getElementById('latency-chart');
            if (canvas) {
                let lastHoveredIndex = -1;

                canvas.addEventListener('mousemove', (e) => {
                    const chart = this.charts.latencyChart;
                    const activeElements = chart.getElementsAtEventForMode(e, 'index', { intersect: false }, false);

                    if (activeElements.length > 0 && selector.value === 'all') {
                        const hoveredIndex = activeElements[0].index;

                        if (hoveredIndex !== lastHoveredIndex) {
                            lastHoveredIndex = hoveredIndex;

                            // Créer les gradients à nouveau
                            const ctx = canvas.getContext('2d');
                            const readLatencyGradient = ctx.createLinearGradient(0, 0, 0, 400);
                            const writeLatencyGradient = ctx.createLinearGradient(0, 0, 0, 400);

                            // Appliquer l'effet de surbrillance
                            chart.data.datasets[0].backgroundColor = this.latencyInstancesData.map((_, idx) => {
                                if (idx === hoveredIndex) {
                                    // Barre surbrillante (Read Latency)
                                    readLatencyGradient.addColorStop(0, 'rgba(251, 146, 60, 1)');
                                    readLatencyGradient.addColorStop(0.5, 'rgba(249, 115, 22, 1)');
                                    readLatencyGradient.addColorStop(1, 'rgba(234, 88, 12, 0.95)');
                                    return readLatencyGradient;
                                } else {
                                    // Barre atténuée (Read Latency)
                                    return 'rgba(251, 146, 60, 0.3)';
                                }
                            });

                            chart.data.datasets[1].backgroundColor = this.latencyInstancesData.map((_, idx) => {
                                if (idx === hoveredIndex) {
                                    // Barre surbrillante (Write Latency)
                                    writeLatencyGradient.addColorStop(0, 'rgba(167, 139, 250, 1)');
                                    writeLatencyGradient.addColorStop(0.5, 'rgba(139, 92, 246, 1)');
                                    writeLatencyGradient.addColorStop(1, 'rgba(124, 58, 237, 0.95)');
                                    return writeLatencyGradient;
                                } else {
                                    // Barre atténuée (Write Latency)
                                    return 'rgba(139, 92, 246, 0.3)';
                                }
                            });

                            chart.data.datasets[0].borderWidth = this.latencyInstancesData.map((_, idx) => idx === hoveredIndex ? 3 : 2);
                            chart.data.datasets[1].borderWidth = this.latencyInstancesData.map((_, idx) => idx === hoveredIndex ? 3 : 2);

                            chart.update('none');
                        }
                    }
                });

                canvas.addEventListener('mouseleave', () => {
                    if (selector.value === 'all') {
                        lastHoveredIndex = -1;
                        const chart = this.charts.latencyChart;
                        const ctx = canvas.getContext('2d');

                        // Restaurer les gradients normaux
                        const readLatencyGradient = ctx.createLinearGradient(0, 0, 0, 400);
                        readLatencyGradient.addColorStop(0, 'rgba(251, 146, 60, 0.95)');
                        readLatencyGradient.addColorStop(0.5, 'rgba(249, 115, 22, 0.9)');
                        readLatencyGradient.addColorStop(1, 'rgba(234, 88, 12, 0.85)');

                        const writeLatencyGradient = ctx.createLinearGradient(0, 0, 0, 400);
                        writeLatencyGradient.addColorStop(0, 'rgba(167, 139, 250, 0.95)');
                        writeLatencyGradient.addColorStop(0.5, 'rgba(139, 92, 246, 0.9)');
                        writeLatencyGradient.addColorStop(1, 'rgba(124, 58, 237, 0.85)');

                        chart.data.datasets[0].backgroundColor = readLatencyGradient;
                        chart.data.datasets[1].backgroundColor = writeLatencyGradient;
                        chart.data.datasets[0].borderWidth = 2;
                        chart.data.datasets[1].borderWidth = 2;

                        chart.update('none');
                    }
                });
            }
        }
    }

    /**
     * Affiche le tableau des instances
     */
    displayInstancesTable() {
        const tbody = document.getElementById('instances-table-body');
        const noInstances = document.getElementById('no-instances');

        if (!tbody) return;

        // Appliquer le filtre de région
        let instances = this.rdsStats.instances;
        if (this.currentRegionFilter !== 'all') {
            instances = instances.filter(i => i.region === this.currentRegionFilter);
        }

        if (instances.length === 0) {
            tbody.innerHTML = '';
            if (noInstances) noInstances.classList.remove('hidden');
            return;
        }

        if (noInstances) noInstances.classList.add('hidden');

        tbody.innerHTML = instances.map(instance => `
            <tr class="border-b border-slate-700 hover:bg-slate-800/50 cursor-pointer transition-colors" onclick="dashboardRDS.showInstanceDetails('${instance.db_instance_identifier}')">
                <td class="py-3">
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-primary text-lg">database</span>
                        <span class="font-mono text-sm">${instance.db_instance_identifier}</span>
                    </div>
                </td>
                <td class="py-3">
                    <span class="px-2 py-1 rounded text-xs font-medium ${this.getEngineColor(instance.engine)}">
                        ${instance.engine?.toUpperCase() || 'N/A'}
                    </span>
                </td>
                <td class="py-3">${instance.engine_version || 'N/A'}</td>
                <td class="py-3">
                    <span class="px-2 py-1 rounded text-xs font-medium ${this.getStatusColor(instance.db_instance_status)}">
                        ${instance.db_instance_status || 'unknown'}
                    </span>
                </td>
                <td class="py-3">${instance.region || 'N/A'}</td>
                <td class="py-3 text-center">${instance.allocated_storage || 0} GB</td>
                <td class="py-3 text-center">
                    ${instance.storage_encrypted
                        ? '<span class="material-symbols-outlined text-success text-lg">lock</span>'
                        : '<span class="material-symbols-outlined text-danger text-lg">lock_open</span>'}
                </td>
                <td class="py-3 text-center">
                    ${instance.multi_az
                        ? '<span class="material-symbols-outlined text-success text-lg">check_circle</span>'
                        : '<span class="material-symbols-outlined text-slate-600 text-lg">cancel</span>'}
                </td>
            </tr>
        `).join('');
    }

    /**
     * Retourne la couleur selon le moteur
     */
    getEngineColor(engine) {
        const colors = {
            'postgres': 'bg-blue-500/20 text-blue-400',
            'mysql': 'bg-cyan-500/20 text-cyan-400',
            'mariadb': 'bg-teal-500/20 text-teal-400',
            'oracle': 'bg-red-500/20 text-red-400',
            'sqlserver': 'bg-purple-500/20 text-purple-400',
            'aurora': 'bg-orange-500/20 text-orange-400',
            'aurora-mysql': 'bg-orange-500/20 text-orange-400',
            'aurora-postgresql': 'bg-blue-500/20 text-blue-400'
        };
        return colors[engine] || 'bg-slate-500/20 text-slate-400';
    }

    /**
     * Retourne la couleur selon le statut
     */
    getStatusColor(status) {
        switch (status) {
            case 'available': return 'bg-success/20 text-success';
            case 'stopped': return 'bg-slate-500/20 text-slate-400';
            case 'starting': return 'bg-accent/20 text-accent';
            case 'stopping': return 'bg-warning/20 text-warning';
            case 'failed': return 'bg-danger/20 text-danger';
            default: return 'bg-slate-500/20 text-slate-400';
        }
    }

    /**
     * Initialise les filtres
     */
    initializeFilters() {
        const regionFilter = document.getElementById('region-filter');
        if (regionFilter) {
            // Peupler le filtre de région
            const regions = this.rdsStats.getActiveRegions();
            regionFilter.innerHTML = '<option value="all">Toutes les régions</option>' +
                regions.map(region => `<option value="${region}">${region}</option>`).join('');

            // Écouter les changements
            regionFilter.addEventListener('change', (e) => {
                this.currentRegionFilter = e.target.value;
                this.displayInstancesTable();
            });
        }

        // Bouton refresh
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.init());
        }
    }

    /**
     * Affiche les détails d'une instance dans une modal
     */
    showInstanceDetails(instanceId) {
        const instance = this.rdsStats.instances.find(i => i.db_instance_identifier === instanceId);
        if (!instance) return;

        const modal = document.getElementById('instance-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('modal-content');

        if (!modal || !modalTitle || !modalContent) return;

        modalTitle.textContent = instance.db_instance_identifier;
        modalContent.innerHTML = this.generateInstanceDetailsHTML(instance);

        modal.classList.remove('hidden');

        // Fermer la modal
        const closeBtn = document.getElementById('close-modal');
        if (closeBtn) {
            closeBtn.onclick = () => modal.classList.add('hidden');
        }

        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        };
    }

    /**
     * Génère le HTML des détails d'une instance
     */
    generateInstanceDetailsHTML(instance) {
        const perf = instance.performance || {};

        return `
            <!-- Informations générales -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">info</span>
                    Informations générales
                </h4>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p class="text-slate-400">Identifiant</p>
                        <p class="text-white font-mono">${instance.db_instance_identifier}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Classe d'instance</p>
                        <p class="text-white">${instance.db_instance_class || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Moteur</p>
                        <p class="text-white">${instance.engine || 'N/A'} ${instance.engine_version || ''}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Statut</p>
                        <span class="px-2 py-1 rounded text-xs font-medium ${this.getStatusColor(instance.db_instance_status)}">
                            ${instance.db_instance_status || 'unknown'}
                        </span>
                    </div>
                    <div>
                        <p class="text-slate-400">Région</p>
                        <p class="text-white">${instance.region || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Zone de disponibilité</p>
                        <p class="text-white">${instance.availability_zone || 'N/A'}</p>
                    </div>
                </div>
            </div>

            <!-- Configuration réseau -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">cloud</span>
                    Configuration réseau
                </h4>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p class="text-slate-400">VPC ID</p>
                        <p class="text-white font-mono">${instance.vpc_id || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Subnet Group</p>
                        <p class="text-white">${instance.db_subnet_group_name || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Endpoint</p>
                        <p class="text-white font-mono text-xs">${instance.endpoint_address || 'N/A'}:${instance.endpoint_port || ''}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Accès public</p>
                        <p class="text-white">${instance.publicly_accessible ? '✅ Oui' : '❌ Non'}</p>
                    </div>
                </div>
            </div>

            <!-- Stockage -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">storage</span>
                    Stockage
                </h4>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p class="text-slate-400">Stockage alloué</p>
                        <p class="text-white">${instance.allocated_storage || 0} GB</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Type de stockage</p>
                        <p class="text-white">${instance.storage_type || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Chiffrement</p>
                        <p class="text-white">${instance.storage_encrypted ? '🔒 Activé' : '🔓 Désactivé'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">IOPS provisionnés</p>
                        <p class="text-white">${instance.iops || 'N/A'}</p>
                    </div>
                </div>
            </div>

            <!-- Sécurité et haute disponibilité -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">security</span>
                    Sécurité et haute disponibilité
                </h4>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p class="text-slate-400">Multi-AZ</p>
                        <p class="text-white">${instance.multi_az ? '✅ Activé' : '❌ Désactivé'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Protection suppression</p>
                        <p class="text-white">${instance.deletion_protection ? '✅ Activé' : '❌ Désactivé'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Authentification IAM</p>
                        <p class="text-white">${instance.iam_database_authentication_enabled ? '✅ Activé' : '❌ Désactivé'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Rétention backup</p>
                        <p class="text-white">${instance.backup_retention_period || 0} jours</p>
                    </div>
                </div>
            </div>

            <!-- Métriques de performance -->
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">speed</span>
                    Métriques de performance
                </h4>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p class="text-slate-400">CPU moyen</p>
                        <p class="text-white">${perf.cpu_utilization_avg?.toFixed(2) || 'N/A'}%</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Connexions actives</p>
                        <p class="text-white">${perf.database_connections || 0}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">IOPS lecture</p>
                        <p class="text-white">${perf.read_iops_avg?.toFixed(2) || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">IOPS écriture</p>
                        <p class="text-white">${perf.write_iops_avg?.toFixed(2) || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Latence lecture</p>
                        <p class="text-white">${perf.read_latency_avg ? (perf.read_latency_avg * 1000).toFixed(2) + ' ms' : 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Latence écriture</p>
                        <p class="text-white">${perf.write_latency_avg ? (perf.write_latency_avg * 1000).toFixed(2) + ' ms' : 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Mémoire disponible</p>
                        <p class="text-white">${perf.freeable_memory_bytes ? (perf.freeable_memory_bytes / 1024 / 1024).toFixed(0) + ' MB' : 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-slate-400">Stockage disponible</p>
                        <p class="text-white">${perf.free_storage_space_bytes ? (perf.free_storage_space_bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB' : 'N/A'}</p>
                    </div>
                </div>
            </div>

            <!-- Tags -->
            ${instance.tags && Object.keys(instance.tags).length > 0 ? `
            <div class="space-y-3">
                <h4 class="text-white font-semibold flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">label</span>
                    Tags
                </h4>
                <div class="flex flex-wrap gap-2">
                    ${Object.entries(instance.tags).map(([key, value]) => `
                        <span class="px-3 py-1 rounded-full bg-slate-700 text-slate-300 text-xs">
                            <span class="font-semibold">${key}:</span> ${value}
                        </span>
                    `).join('')}
                </div>
            </div>
            ` : ''}
        `;
    }
}

// Instance globale
const dashboardRDS = new DashboardRDS();


