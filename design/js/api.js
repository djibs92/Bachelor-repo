/**
 * Fonctions pour interagir avec l'API CloudDiagnoze
 */

class CloudDiagnozeAPI {
    constructor() {
        this.baseURL = API_CONFIG.BASE_URL;
    }

    /**
     * Fonction générique pour faire des requêtes HTTP
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        // Récupérer le token JWT depuis authManager
        const token = authManager ? authManager.getToken() : null;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` }),  // ✅ AJOUT DU TOKEN JWT
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Erreur lors de la requête ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Récupère l'historique des scans
     */
    async getScansHistory(params = {}) {
        const queryParams = new URLSearchParams({
            limit: params.limit || 100,
            ...(params.client_id && { client_id: params.client_id }),
            ...(params.service_type && { service_type: params.service_type })
        });

        return await this.request(`${API_CONFIG.ENDPOINTS.SCANS_HISTORY}?${queryParams}`);
    }

    /**
     * Alias pour getScansHistory (pour compatibilité)
     */
    async getScanRuns(params = {}) {
        return await this.getScansHistory(params);
    }

    /**
     * Récupère les instances EC2
     */
    async getEC2Instances(params = {}) {
        const queryParams = new URLSearchParams({
            limit: params.limit || 100,
            latest_only: params.latest_only !== undefined ? params.latest_only : true,
            ...(params.client_id && { client_id: params.client_id }),
            ...(params.region && { region: params.region }),
            ...(params.state && { state: params.state })
        });

        return await this.request(`${API_CONFIG.ENDPOINTS.EC2_INSTANCES}?${queryParams}`);
    }

    /**
     * Récupère une instance EC2 spécifique
     */
    async getEC2InstanceById(instanceId) {
        return await this.request(`${API_CONFIG.ENDPOINTS.EC2_INSTANCE_BY_ID}/${instanceId}`);
    }

    /**
     * Récupère les buckets S3
     */
    async getS3Buckets(params = {}) {
        const queryParams = new URLSearchParams({
            limit: params.limit || 100,
            latest_only: params.latest_only !== undefined ? params.latest_only : true,
            ...(params.client_id && { client_id: params.client_id }),
            ...(params.region && { region: params.region })
        });

        return await this.request(`${API_CONFIG.ENDPOINTS.S3_BUCKETS}?${queryParams}`);
    }

    /**
     * Récupère un bucket S3 spécifique
     */
    async getS3BucketByName(bucketName) {
        return await this.request(`${API_CONFIG.ENDPOINTS.S3_BUCKET_BY_NAME}/${bucketName}`);
    }

    /**
     * Récupère toutes les ressources (EC2 + S3)
     */
    async getAllResources(params = {}) {
        try {
            const [ec2Data, s3Data] = await Promise.all([
                this.getEC2Instances(params),
                this.getS3Buckets(params)
            ]);

            return {
                ec2: ec2Data,
                s3: s3Data,
                total: (ec2Data.total_instances || 0) + (s3Data.total_buckets || 0)
            };
        } catch (error) {
            console.error('Erreur lors de la récupération des ressources:', error);
            throw error;
        }
    }

    /**
     * Calcule les statistiques du dashboard
     */
    async getDashboardStats(params = {}) {
        try {
            const [scansData, resourcesData] = await Promise.all([
                this.getScansHistory(params),
                this.getAllResources(params)
            ]);

            // Calculer les scans du mois en cours
            const now = new Date();
            const currentMonth = now.getMonth();
            const currentYear = now.getFullYear();
            
            const scansThisMonth = scansData.scans.filter(scan => {
                const scanDate = new Date(scan.scan_timestamp);
                return scanDate.getMonth() === currentMonth && 
                       scanDate.getFullYear() === currentYear;
            }).length;

            // Calculer la moyenne CPU des instances EC2
            let avgCPU = 0;
            if (resourcesData.ec2.instances && resourcesData.ec2.instances.length > 0) {
                const cpuValues = resourcesData.ec2.instances
                    .filter(instance => instance.performance && instance.performance.cpu_utilization_avg)
                    .map(instance => instance.performance.cpu_utilization_avg);
                
                if (cpuValues.length > 0) {
                    avgCPU = cpuValues.reduce((sum, val) => sum + val, 0) / cpuValues.length;
                }
            }

            // Distribution des ressources par provider
            const distribution = {
                aws: resourcesData.total,
                gcp: 0,  // Pas encore implémenté
                azure: 0  // Pas encore implémenté
            };

            return {
                totalResources: resourcesData.total,
                scansThisMonth: scansThisMonth,
                totalScans: scansData.total_scans,
                activeAlerts: 0,  // À implémenter plus tard
                monthlyCost: 0,   // À implémenter plus tard
                avgCPU: avgCPU.toFixed(2),
                distribution: distribution,
                ec2Count: resourcesData.ec2.total_instances || 0,
                s3Count: resourcesData.s3.total_buckets || 0
            };
        } catch (error) {
            console.error('Erreur lors du calcul des statistiques:', error);
            throw error;
        }
    }
}

// Créer une instance globale de l'API
const api = new CloudDiagnozeAPI();

