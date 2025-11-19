/**
 * Scan History Manager
 * Gère l'affichage et la navigation dans l'historique des scans
 */
class ScanHistoryManager {
    constructor() {
        this.allScans = [];
        this.filteredScans = [];
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.evolutionChart = null;
    }

    /**
     * Initialisation
     */
    async init() {
        console.log('🚀 Initialisation Scan History...');
        
        // Charger les données
        await this.loadScans();
        
        // Créer le graphique d'évolution
        this.createEvolutionChart();
        
        // Initialiser les filtres
        this.initializeFilters();
        
        // Afficher les scans
        this.applyFilters();
        
        console.log('✅ Scan History initialisé');
    }

    /**
     * Charge tous les scans depuis l'API
     */
    async loadScans() {
        try {
            console.log('🔄 Chargement des scans depuis l\'API...');
            const data = await api.getScansHistory({ limit: 1000 });
            console.log('📊 Réponse API complète:', data);
            console.log('📊 Nombre de scans reçus:', data.scans ? data.scans.length : 0);

            this.allScans = data.scans || [];
            this.filteredScans = [...this.allScans];

            console.log('✅ allScans:', this.allScans.length, 'scans');
            console.log('✅ filteredScans:', this.filteredScans.length, 'scans');

            if (this.allScans.length > 0) {
                console.log('📋 Premier scan:', this.allScans[0]);
            }

        } catch (error) {
            console.error('❌ Erreur chargement scans:', error);
            this.showNotification('Erreur lors du chargement des scans', 'error');
        }
    }

    /**
     * Crée le graphique d'évolution des ressources
     */
    createEvolutionChart() {
        const ctx = document.getElementById('evolution-chart');
        if (!ctx) return;

        // Grouper les scans par jour et compter les ressources
        const scansByDay = this.groupScansByDay(this.allScans);
        
        const labels = Object.keys(scansByDay).sort();
        const ec2Data = labels.map(date => scansByDay[date].ec2 || 0);
        const s3Data = labels.map(date => scansByDay[date].s3 || 0);
        const vpcData = labels.map(date => scansByDay[date].vpc || 0);

        this.evolutionChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels.map(date => {
                    const d = new Date(date);
                    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
                }),
                datasets: [
                    {
                        label: 'EC2 Instances',
                        data: ec2Data,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'S3 Buckets',
                        data: s3Data,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'VPC Networks',
                        data: vpcData,
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { color: '#cbd5e1', font: { size: 12 } }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#cbd5e1',
                        borderColor: '#334155',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: { color: '#1e293b' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { color: '#1e293b' },
                        ticks: { color: '#94a3b8' },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    /**
     * Groupe les scans par jour
     */
    groupScansByDay(scans) {
        const grouped = {};
        
        scans.forEach(scan => {
            const date = new Date(scan.scan_timestamp).toISOString().split('T')[0];
            
            if (!grouped[date]) {
                grouped[date] = { ec2: 0, s3: 0, vpc: 0 };
            }
            
            const service = scan.service_type.toLowerCase();
            if (grouped[date][service] !== undefined) {
                grouped[date][service] += scan.total_resources || 0;
            }
        });
        
        return grouped;
    }

    /**
     * Initialise les filtres et événements
     */
    initializeFilters() {
        // Filtres
        document.getElementById('filter-service')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('filter-period')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('filter-status')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('search-id')?.addEventListener('input', () => this.applyFilters());

        // Bouton refresh
        document.getElementById('refresh-btn')?.addEventListener('click', () => this.init());

        // Modal
        document.getElementById('close-modal')?.addEventListener('click', () => this.closeModal());
        document.getElementById('modal-scan-details')?.addEventListener('click', (e) => {
            if (e.target.id === 'modal-scan-details') this.closeModal();
        });
    }

    /**
     * Applique les filtres
     */
    applyFilters() {
        console.log('🔍 Application des filtres...');
        console.log('📊 allScans avant filtrage:', this.allScans.length);

        const serviceFilter = document.getElementById('filter-service')?.value || 'all';
        const periodFilter = document.getElementById('filter-period')?.value || 'all';
        const statusFilter = document.getElementById('filter-status')?.value || 'all';
        const searchId = document.getElementById('search-id')?.value.trim() || '';

        console.log('🔧 Filtres actifs:', { serviceFilter, periodFilter, statusFilter, searchId });

        this.filteredScans = this.allScans.filter(scan => {
            // Filtre service
            if (serviceFilter !== 'all' && scan.service_type.toLowerCase() !== serviceFilter) {
                return false;
            }

            // Filtre période
            if (periodFilter !== 'all') {
                const scanDate = new Date(scan.scan_timestamp);
                const now = new Date();

                switch (periodFilter) {
                    case 'today':
                        if (scanDate.toDateString() !== now.toDateString()) return false;
                        break;
                    case 'week':
                        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                        if (scanDate < weekAgo) return false;
                        break;
                    case 'month':
                        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                        if (scanDate < monthAgo) return false;
                        break;
                    case 'year':
                        const yearAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
                        if (scanDate < yearAgo) return false;
                        break;
                }
            }

            // Filtre statut
            if (statusFilter !== 'all' && scan.status !== statusFilter) {
                return false;
            }

            // Recherche par ID
            if (searchId && !scan.scan_id.toString().includes(searchId)) {
                return false;
            }

            return true;
        });

        console.log('✅ filteredScans après filtrage:', this.filteredScans.length);

        this.currentPage = 1;
        this.displayScans();
    }

    /**
     * Affiche les scans avec pagination
     */
    displayScans() {
        console.log('📺 displayScans() appelé');
        const tbody = document.getElementById('scans-table-body');
        if (!tbody) {
            console.error('❌ Element scans-table-body non trouvé !');
            return;
        }

        console.log('✅ tbody trouvé');

        // Grouper les scans par timestamp (même scan = plusieurs services)
        const groupedScans = this.groupScansByTimestamp(this.filteredScans);
        console.log('📦 Scans groupés:', groupedScans.length, 'groupes');

        // Pagination
        const totalPages = Math.ceil(groupedScans.length / this.itemsPerPage);
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageScans = groupedScans.slice(startIndex, endIndex);

        console.log('📄 Page actuelle:', this.currentPage, '- Scans à afficher:', pageScans.length);

        // Afficher les scans
        if (pageScans.length === 0) {
            console.log('⚠️ Aucun scan à afficher');
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-12 text-center">
                        <div class="flex flex-col items-center gap-3">
                            <span class="material-symbols-outlined text-slate-600 text-6xl">search_off</span>
                            <p class="text-slate-400 text-lg">Aucun scan trouvé</p>
                            <p class="text-slate-500 text-sm">Essayez de modifier les filtres</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = '';
        pageScans.forEach((scanGroup, index) => {
            console.log(`➕ Ajout du scan ${index + 1}:`, scanGroup);
            const row = this.createScanRow(scanGroup);
            tbody.appendChild(row);
        });

        console.log('✅ Tous les scans ajoutés au tableau');

        // Mettre à jour la pagination
        this.updatePagination(groupedScans.length, totalPages);
    }

    /**
     * Groupe les scans par timestamp
     */
    groupScansByTimestamp(scans) {
        const sorted = [...scans].sort((a, b) =>
            new Date(b.scan_timestamp) - new Date(a.scan_timestamp)
        );

        const groups = [];
        const timeThreshold = 60000; // 1 minute

        sorted.forEach(scan => {
            const scanTime = new Date(scan.scan_timestamp).getTime();

            let group = groups.find(g =>
                Math.abs(new Date(g.timestamp).getTime() - scanTime) < timeThreshold
            );

            if (!group) {
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
     * Crée une ligne de tableau pour un scan
     */
    createScanRow(scanGroup) {
        const row = document.createElement('tr');
        row.className = 'border-b border-slate-700 hover:bg-slate-800/50 transition-colors';

        const date = new Date(scanGroup.timestamp);
        const formattedDate = date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
        const formattedTime = date.toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
        });

        // Services scannés
        const services = scanGroup.scans.map(s => {
            const color = s.service_type === 'ec2' ? 'bg-blue-500' :
                         s.service_type === 's3' ? 'bg-green-500' : 'bg-purple-500';
            return `<span class="px-2 py-1 rounded text-xs font-semibold ${color}">${s.service_type.toUpperCase()}</span>`;
        }).join(' ');

        // Total ressources
        const totalResources = scanGroup.scans.reduce((sum, s) => sum + (s.total_resources || 0), 0);

        // Statut global
        const hasFailure = scanGroup.scans.some(s => s.status === 'failed');
        const hasPartial = scanGroup.scans.some(s => s.status === 'partial');
        const status = hasFailure ? 'failed' : hasPartial ? 'partial' : 'success';

        const statusConfig = {
            success: { color: 'text-green-400', bg: 'bg-green-500/10', icon: 'check_circle', text: 'Succès' },
            failed: { color: 'text-red-400', bg: 'bg-red-500/10', icon: 'error', text: 'Échec' },
            partial: { color: 'text-orange-400', bg: 'bg-orange-500/10', icon: 'warning', text: 'Partiel' }
        };
        const statusInfo = statusConfig[status];

        row.innerHTML = `
            <td class="px-6 py-4">
                <span class="font-mono text-primary font-semibold">#${scanGroup.id}</span>
            </td>
            <td class="px-6 py-4">
                <div class="flex flex-col">
                    <span class="text-white font-medium">${formattedDate}</span>
                    <span class="text-slate-400 text-sm">${formattedTime}</span>
                </div>
            </td>
            <td class="px-6 py-4">
                <div class="flex gap-2 flex-wrap">${services}</div>
            </td>
            <td class="px-6 py-4">
                <span class="text-white font-semibold">${totalResources}</span>
            </td>
            <td class="px-6 py-4">
                <div class="flex items-center gap-2 ${statusInfo.bg} ${statusInfo.color} px-3 py-1 rounded-full w-fit">
                    <span class="material-symbols-outlined text-sm">${statusInfo.icon}</span>
                    <span class="text-sm font-medium">${statusInfo.text}</span>
                </div>
            </td>
            <td class="px-6 py-4">
                <div class="flex gap-2">
                    <button class="btn-icon" title="Voir détails" data-action="details">
                        <span class="material-symbols-outlined">visibility</span>
                    </button>
                    <button class="btn-icon btn-primary" title="Charger dans Dashboard" data-action="load">
                        <span class="material-symbols-outlined">dashboard</span>
                    </button>
                    <button class="btn-icon btn-success" title="Télécharger JSON" data-action="download">
                        <span class="material-symbols-outlined">download</span>
                    </button>
                </div>
            </td>
        `;

        // Événements
        row.querySelector('[data-action="details"]').addEventListener('click', () => this.showScanDetails(scanGroup));
        row.querySelector('[data-action="load"]').addEventListener('click', () => this.loadScanInDashboard(scanGroup));
        row.querySelector('[data-action="download"]').addEventListener('click', () => this.downloadScanJSON(scanGroup));

        return row;
    }

    /**
     * Met à jour la pagination
     */
    updatePagination(totalItems, totalPages) {
        const paginationInfo = document.getElementById('pagination-info');
        const paginationControls = document.getElementById('pagination-controls');

        if (paginationInfo) {
            const startItem = (this.currentPage - 1) * this.itemsPerPage + 1;
            const endItem = Math.min(this.currentPage * this.itemsPerPage, totalItems);
            paginationInfo.textContent = `Affichage de ${startItem}-${endItem} sur ${totalItems} scans`;
        }

        if (paginationControls) {
            paginationControls.innerHTML = '';

            // Bouton précédent
            const prevBtn = document.createElement('button');
            prevBtn.className = `px-3 py-1 rounded ${this.currentPage === 1 ? 'bg-slate-800 text-slate-600 cursor-not-allowed' : 'bg-slate-700 text-white hover:bg-slate-600'}`;
            prevBtn.textContent = 'Précédent';
            prevBtn.disabled = this.currentPage === 1;
            prevBtn.addEventListener('click', () => {
                if (this.currentPage > 1) {
                    this.currentPage--;
                    this.displayScans();
                }
            });
            paginationControls.appendChild(prevBtn);

            // Numéros de page
            for (let i = 1; i <= totalPages; i++) {
                if (i === 1 || i === totalPages || (i >= this.currentPage - 1 && i <= this.currentPage + 1)) {
                    const pageBtn = document.createElement('button');
                    pageBtn.className = `px-3 py-1 rounded ${i === this.currentPage ? 'bg-primary text-white' : 'bg-slate-700 text-white hover:bg-slate-600'}`;
                    pageBtn.textContent = i;
                    pageBtn.addEventListener('click', () => {
                        this.currentPage = i;
                        this.displayScans();
                    });
                    paginationControls.appendChild(pageBtn);
                } else if (i === this.currentPage - 2 || i === this.currentPage + 2) {
                    const dots = document.createElement('span');
                    dots.className = 'px-2 text-slate-500';
                    dots.textContent = '...';
                    paginationControls.appendChild(dots);
                }
            }

            // Bouton suivant
            const nextBtn = document.createElement('button');
            nextBtn.className = `px-3 py-1 rounded ${this.currentPage === totalPages ? 'bg-slate-800 text-slate-600 cursor-not-allowed' : 'bg-slate-700 text-white hover:bg-slate-600'}`;
            nextBtn.textContent = 'Suivant';
            nextBtn.disabled = this.currentPage === totalPages;
            nextBtn.addEventListener('click', () => {
                if (this.currentPage < totalPages) {
                    this.currentPage++;
                    this.displayScans();
                }
            });
            paginationControls.appendChild(nextBtn);
        }
    }

    /**
     * Affiche les détails d'un scan dans un modal
     */
    showScanDetails(scanGroup) {
        const modal = document.getElementById('modal-scan-details');
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('modal-content');

        const date = new Date(scanGroup.timestamp);
        const formattedDate = date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        modalTitle.innerHTML = `
            <span class="material-symbols-outlined text-primary">info</span>
            Scan #${scanGroup.id} - ${formattedDate}
        `;

        let content = '';
        scanGroup.scans.forEach(scan => {
            const serviceColor = scan.service_type === 'ec2' ? 'text-blue-400' :
                                scan.service_type === 's3' ? 'text-green-400' : 'text-purple-400';
            const statusColor = scan.status === 'success' ? 'text-green-400' :
                               scan.status === 'failed' ? 'text-red-400' : 'text-orange-400';

            content += `
                <div class="glass-card p-4 border border-slate-700">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="text-xl font-bold ${serviceColor}">${scan.service_type.toUpperCase()}</h3>
                        <span class="text-sm ${statusColor} font-semibold">${scan.status}</span>
                    </div>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <p class="text-slate-400">Ressources trouvées</p>
                            <p class="text-white font-semibold text-lg">${scan.total_resources || 0}</p>
                        </div>
                        <div>
                            <p class="text-slate-400">Scan ID</p>
                            <p class="text-white font-mono">${scan.scan_id}</p>
                        </div>
                    </div>
                </div>
            `;
        });

        modalContent.innerHTML = content;
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    /**
     * Charge un scan dans le Dashboard Global
     */
    loadScanInDashboard(scanGroup) {
        // Rediriger vers le Dashboard Global avec le premier scan_id du groupe
        // Le dashboard chargera tous les scans de cette session (fenêtre de 5 minutes)
        const firstScanId = scanGroup.scans[0]?.scan_id || scanGroup.id;
        window.location.href = `dashbord.html?scan_id=${firstScanId}`;
    }

    /**
     * Ferme le modal
     */
    closeModal() {
        const modal = document.getElementById('modal-scan-details');
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }

    /**
     * Affiche une notification
     */
    showNotification(message, type = 'info') {
        // Utiliser le système de notification existant si disponible
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    /**
     * Télécharge les détails complets d'un scan en JSON
     */
    async downloadScanJSON(scanGroup) {
        console.log('📥 Téléchargement du scan en JSON:', scanGroup);

        try {
            // Appeler l'API pour récupérer les détails complets
            const token = authManager ? authManager.getToken() : localStorage.getItem('clouddiagnoze_token');
            const response = await fetch(`${API_CONFIG.BASE_URL}/scans/${scanGroup.id}/export`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Erreur API: ${response.status} ${response.statusText}`);
            }

            const exportData = await response.json();

            // Convertir en JSON formaté
            const jsonString = JSON.stringify(exportData, null, 2);

            // Créer un blob
            const blob = new Blob([jsonString], { type: 'application/json' });

            // Créer un lien de téléchargement
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            // Nom du fichier avec timestamp
            const date = new Date(scanGroup.timestamp);
            const dateStr = date.toISOString().split('T')[0];
            const timeStr = date.toTimeString().split(' ')[0].replace(/:/g, '-');
            a.download = `scan-${scanGroup.id}-${dateStr}-${timeStr}.json`;

            // Déclencher le téléchargement
            document.body.appendChild(a);
            a.click();

            // Nettoyer
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            console.log('✅ Scan exporté en JSON:', scanGroup.id);

        } catch (error) {
            console.error('❌ Erreur lors du téléchargement:', error);

            // L'erreur 401 est déjà gérée dans api.js
            // Afficher juste un message pour les autres erreurs
            if (!error.message.includes('Session expirée')) {
                alert(`Erreur lors du téléchargement du scan: ${error.message}`);
            }
        }
    }
}

// Initialisation au chargement de la page
const scanHistoryManager = new ScanHistoryManager();

document.addEventListener('DOMContentLoaded', async () => {
    // Vérifier l'authentification
    if (!authManager || !authManager.isAuthenticated()) {
        console.log('❌ Utilisateur non authentifié, redirection vers login...');
        window.location.href = 'login.html';
        return;
    }

    console.log('✅ Utilisateur authentifié');

    // Charger les informations utilisateur pour le header
    try {
        const result = await authManager.getCurrentUser();
        console.log('✅ Résultat getCurrentUser:', result);

        if (!result.success) {
            console.error('❌ Échec récupération utilisateur:', result.error);
            return;
        }

        const user = result.user;
        console.log('✅ Utilisateur chargé:', user);

        // Mettre à jour le header
        const userNameHeader = document.getElementById('user-name-header');
        const userEmailHeader = document.getElementById('user-email-header');

        if (userNameHeader) {
            userNameHeader.textContent = user.full_name || 'Utilisateur';
        }
        if (userEmailHeader) {
            userEmailHeader.textContent = user.email;
        }

        console.log('🔧 Initialisation du menu utilisateur...');

        // Initialiser le menu utilisateur popup
        if (window.userMenu) {
            window.userMenu.init(user);
            console.log('✅ Menu utilisateur initialisé');
        } else {
            console.warn('⚠️ window.userMenu non disponible');
        }
    } catch (error) {
        console.error('❌ Erreur lors de la récupération des infos utilisateur:', error);
        // Ne pas déconnecter ici, laisser l'utilisateur utiliser la page
    }

    // Initialiser le gestionnaire d'historique
    try {
        await scanHistoryManager.init();
        console.log('✅ Scan History Manager initialisé avec succès');
    } catch (error) {
        console.error('❌ Erreur initialisation scan history:', error);
    }

    // Event listener pour le bouton refresh
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            console.log('🔄 Rafraîchissement de l\'historique...');
            await scanHistoryManager.loadScans();
            scanHistoryManager.applyFilters();
        });
    }
});

