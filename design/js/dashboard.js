/**
 * Logique du Dashboard CloudDiagnoze
 */

class Dashboard {
    constructor() {
        this.isLoading = false;
        this.stats = null;
    }

    /**
     * Initialise le dashboard au chargement de la page
     */
    async init() {
        console.log('🚀 Initialisation du dashboard...');
        
        // Afficher un loader
        this.showLoader();
        
        try {
            // Charger les données
            await this.loadDashboardData();
            
            // Masquer le loader
            this.hideLoader();
            
            console.log('✅ Dashboard chargé avec succès');
        } catch (error) {
            console.error('❌ Erreur lors du chargement du dashboard:', error);
            this.showError('Impossible de charger les données du dashboard');
            this.hideLoader();
        }
    }

    /**
     * Charge toutes les données du dashboard
     */
    async loadDashboardData() {
        try {
            // Récupérer les statistiques
            this.stats = await api.getDashboardStats({
                client_id: API_CONFIG.DEFAULT_CLIENT_ID
            });

            console.log('📊 Statistiques récupérées:', this.stats);

            // Mettre à jour l'interface
            this.updateStatsCards();
            this.updateCPUChart();
            this.updateResourceDistribution();
            
        } catch (error) {
            console.error('Erreur lors du chargement des données:', error);
            throw error;
        }
    }

    /**
     * Met à jour les cartes de statistiques
     */
    updateStatsCards() {
        // Total Resources
        const totalResourcesEl = document.getElementById('total-resources');
        if (totalResourcesEl) {
            totalResourcesEl.textContent = this.formatNumber(this.stats.totalResources);
        }

        // Scans This Month
        const scansMonthEl = document.getElementById('scans-month');
        if (scansMonthEl) {
            scansMonthEl.textContent = this.formatNumber(this.stats.scansThisMonth);
        }

        // Active Alerts (pas encore implémenté)
        const activeAlertsEl = document.getElementById('active-alerts');
        if (activeAlertsEl) {
            activeAlertsEl.textContent = this.formatNumber(this.stats.activeAlerts);
        }

        // Monthly Cost (pas encore implémenté)
        const monthlyCostEl = document.getElementById('monthly-cost');
        if (monthlyCostEl) {
            monthlyCostEl.textContent = `$${this.formatNumber(this.stats.monthlyCost)}`;
        }

        console.log('✅ Cartes de stats mises à jour');
    }

    /**
     * Met à jour le graphique CPU
     */
    updateCPUChart() {
        const cpuValueEl = document.getElementById('cpu-value');
        if (cpuValueEl) {
            cpuValueEl.textContent = `${this.stats.avgCPU}%`;
        }

        // TODO: Mettre à jour le graphique SVG avec les vraies données
        console.log('✅ Graphique CPU mis à jour');
    }

    /**
     * Met à jour la distribution des ressources
     */
    updateResourceDistribution() {
        // Calculer les pourcentages
        const total = this.stats.totalResources;
        const awsPercent = total > 0 ? ((this.stats.distribution.aws / total) * 100).toFixed(0) : 0;
        const gcpPercent = total > 0 ? ((this.stats.distribution.gcp / total) * 100).toFixed(0) : 0;
        const azurePercent = total > 0 ? ((this.stats.distribution.azure / total) * 100).toFixed(0) : 0;

        // Mettre à jour les pourcentages dans l'interface
        const awsPercentEl = document.getElementById('aws-percent');
        const gcpPercentEl = document.getElementById('gcp-percent');
        const azurePercentEl = document.getElementById('azure-percent');

        if (awsPercentEl) awsPercentEl.textContent = `${awsPercent}%`;
        if (gcpPercentEl) gcpPercentEl.textContent = `${gcpPercent}%`;
        if (azurePercentEl) azurePercentEl.textContent = `${azurePercent}%`;

        // Mettre à jour le total dans le donut
        const totalDonutEl = document.getElementById('total-resources-donut');
        if (totalDonutEl) totalDonutEl.textContent = this.formatNumber(total);

        // Mettre à jour les compteurs
        const awsCountEl = document.getElementById('aws-count');
        const gcpCountEl = document.getElementById('gcp-count');
        const azureCountEl = document.getElementById('azure-count');

        if (awsCountEl) awsCountEl.textContent = this.stats.distribution.aws;
        if (gcpCountEl) gcpCountEl.textContent = this.stats.distribution.gcp;
        if (azureCountEl) azureCountEl.textContent = this.stats.distribution.azure;

        console.log('✅ Distribution des ressources mise à jour');
    }

    /**
     * Affiche un loader
     */
    showLoader() {
        this.isLoading = true;
        const loaderEl = document.getElementById('dashboard-loader');
        if (loaderEl) {
            loaderEl.classList.remove('hidden');
        }
    }

    /**
     * Masque le loader
     */
    hideLoader() {
        this.isLoading = false;
        const loaderEl = document.getElementById('dashboard-loader');
        if (loaderEl) {
            loaderEl.classList.add('hidden');
        }
    }

    /**
     * Affiche un message d'erreur
     */
    showError(message) {
        // Créer une notification d'erreur
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-500/10 border border-red-500 text-red-500 px-6 py-4 rounded-lg backdrop-blur-sm z-50';
        errorDiv.innerHTML = `
            <div class="flex items-center gap-3">
                <span class="material-symbols-outlined">error</span>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Supprimer après 5 secondes
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    /**
     * Formate un nombre avec des séparateurs de milliers
     */
    formatNumber(num) {
        return new Intl.NumberFormat('fr-FR').format(num);
    }

    /**
     * Rafraîchit les données du dashboard
     */
    async refresh() {
        console.log('🔄 Rafraîchissement du dashboard...');
        await this.loadDashboardData();
    }
}

// Créer une instance globale du dashboard
const dashboard = new Dashboard();

// Initialiser le dashboard au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    dashboard.init();
});

// Rafraîchir toutes les 30 secondes
setInterval(() => {
    if (!dashboard.isLoading) {
        dashboard.refresh();
    }
}, 30000);

