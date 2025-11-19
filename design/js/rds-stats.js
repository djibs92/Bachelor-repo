/**
 * Classe pour calculer les statistiques des instances RDS
 */

class RDSStats {
    constructor() {
        this.instances = [];
        this.scanId = null;
        this.scanTimestamp = null;
    }

    /**
     * Charge les instances RDS depuis l'API
     */
    async loadInstances(params = {}) {
        try {
            // Vérifier si RDS a été scanné dans la dernière session
            const session = await api.getLatestScanSession();
            const scannedServices = session.services || [];

            if (!scannedServices.includes('rds')) {
                console.log('⚪ RDS non scanné dans la dernière session');
                this.instances = [];
                this.scanId = null;
                this.scanTimestamp = null;
                return this.instances;
            }

            // Récupérer le scan_id RDS de cette session
            const rdsScan = session.scans?.find(s => s.service_type === 'rds');
            if (!rdsScan) {
                console.log('⚪ Aucun scan RDS trouvé dans la session');
                this.instances = [];
                this.scanId = null;
                this.scanTimestamp = null;
                return this.instances;
            }

            // RDS a été scanné, charger les données avec le scan_id spécifique
            console.log('📡 Appel API getRDSInstances avec scan_id:', rdsScan.scan_id);
            const data = await api.getRDSInstances({ ...params, limit: 100, scan_id: rdsScan.scan_id });
            console.log('📦 Données reçues de l\'API:', data);
            this.instances = data.instances || [];
            this.scanId = data.scan_id;
            this.scanTimestamp = data.scan_timestamp;
            console.log(`✅ ${this.instances.length} instances RDS chargées (scan #${rdsScan.scan_id})`);
            return this.instances;
        } catch (error) {
            console.error('❌ Erreur lors du chargement des instances RDS:', error);
            throw error;
        }
    }

    /**
     * Statistiques totales des instances RDS
     */
    getTotalInstancesStats() {
        const total = this.instances.length;
        const running = this.instances.filter(i => i.db_instance_status === 'available').length;
        const stopped = this.instances.filter(i => i.db_instance_status === 'stopped').length;
        const other = total - running - stopped;

        return {
            total,
            running,
            stopped,
            other
        };
    }

    /**
     * Statistiques par région
     */
    getRegionsStats() {
        const regionMap = {};
        
        this.instances.forEach(instance => {
            const region = instance.region || 'unknown';
            if (!regionMap[region]) {
                regionMap[region] = {
                    count: 0,
                    instances: []
                };
            }
            regionMap[region].count++;
            regionMap[region].instances.push(instance);
        });

        return regionMap;
    }

    /**
     * Récupère les régions actives
     */
    getActiveRegions() {
        return [...new Set(this.instances.map(i => i.region))].filter(r => r).sort();
    }

    /**
     * Statistiques par moteur de base de données
     */
    getEngineStats() {
        const engineMap = {};
        
        this.instances.forEach(instance => {
            const engine = instance.engine || 'unknown';
            if (!engineMap[engine]) {
                engineMap[engine] = 0;
            }
            engineMap[engine]++;
        });

        return engineMap;
    }

    /**
     * Statistiques de sécurité
     */
    getSecurityStats() {
        const encrypted = this.instances.filter(i => i.storage_encrypted).length;
        const notEncrypted = this.instances.length - encrypted;
        const publiclyAccessible = this.instances.filter(i => i.publicly_accessible).length;
        const deletionProtection = this.instances.filter(i => i.deletion_protection).length;
        const multiAZ = this.instances.filter(i => i.multi_az).length;
        const iamAuth = this.instances.filter(i => i.iam_database_authentication_enabled).length;

        const encryptionPercentage = this.instances.length > 0 
            ? Math.round((encrypted / this.instances.length) * 100) 
            : 0;

        const securityScore = this.instances.length > 0
            ? Math.round(((encrypted + deletionProtection + multiAZ + iamAuth - publiclyAccessible) / (this.instances.length * 4)) * 100)
            : 0;

        return {
            encrypted,
            notEncrypted,
            encryptionPercentage,
            publiclyAccessible,
            deletionProtection,
            multiAZ,
            iamAuth,
            securityScore: Math.max(0, Math.min(100, securityScore))
        };
    }

    /**
     * Statistiques de stockage
     */
    getStorageStats() {
        const totalStorage = this.instances.reduce((sum, i) => sum + (i.allocated_storage || 0), 0);
        const storageTypes = {};

        this.instances.forEach(instance => {
            const type = instance.storage_type || 'unknown';
            if (!storageTypes[type]) {
                storageTypes[type] = 0;
            }
            storageTypes[type]++;
        });

        return {
            totalStorage,
            storageTypes
        };
    }

    /**
     * Statistiques de performance moyenne
     */
    getPerformanceStats() {
        if (this.instances.length === 0) {
            return {
                avgCPU: 0,
                avgConnections: 0,
                avgReadIOPS: 0,
                avgWriteIOPS: 0
            };
        }

        const totalCPU = this.instances.reduce((sum, i) => sum + (i.performance?.cpu_utilization_avg || 0), 0);
        const totalConnections = this.instances.reduce((sum, i) => sum + (i.performance?.database_connections || 0), 0);
        const totalReadIOPS = this.instances.reduce((sum, i) => sum + (i.performance?.read_iops_avg || 0), 0);
        const totalWriteIOPS = this.instances.reduce((sum, i) => sum + (i.performance?.write_iops_avg || 0), 0);

        return {
            avgCPU: Math.round((totalCPU / this.instances.length) * 100) / 100,
            avgConnections: Math.round(totalConnections / this.instances.length),
            avgReadIOPS: Math.round((totalReadIOPS / this.instances.length) * 100) / 100,
            avgWriteIOPS: Math.round((totalWriteIOPS / this.instances.length) * 100) / 100
        };
    }

    /**
     * Génère des alertes basées sur les données
     */
    generateAlerts() {
        const alerts = [];
        const securityStats = this.getSecurityStats();

        // Alerte: Instances non chiffrées
        if (securityStats.notEncrypted > 0) {
            alerts.push({
                type: 'danger',
                icon: 'lock_open',
                title: 'Stockage non chiffré',
                message: `${securityStats.notEncrypted} instance(s) RDS sans chiffrement`
            });
        }

        // Alerte: Instances publiquement accessibles
        if (securityStats.publiclyAccessible > 0) {
            alerts.push({
                type: 'warning',
                icon: 'public',
                title: 'Accès public activé',
                message: `${securityStats.publiclyAccessible} instance(s) RDS accessible(s) publiquement`
            });
        }

        // Alerte: Pas de protection contre la suppression
        const noProtection = this.instances.length - securityStats.deletionProtection;
        if (noProtection > 0) {
            alerts.push({
                type: 'warning',
                icon: 'delete',
                title: 'Protection suppression désactivée',
                message: `${noProtection} instance(s) sans protection contre la suppression`
            });
        }

        // Alerte: Pas de Multi-AZ
        const noMultiAZ = this.instances.length - securityStats.multiAZ;
        if (noMultiAZ > 0) {
            alerts.push({
                type: 'info',
                icon: 'cloud_off',
                title: 'Multi-AZ désactivé',
                message: `${noMultiAZ} instance(s) sans haute disponibilité Multi-AZ`
            });
        }

        // Alerte: CPU élevé
        const highCPU = this.instances.filter(i => (i.performance?.cpu_utilization_avg || 0) > 80);
        if (highCPU.length > 0) {
            alerts.push({
                type: 'warning',
                icon: 'speed',
                title: 'CPU élevé',
                message: `${highCPU.length} instance(s) avec CPU > 80%`
            });
        }

        return alerts;
    }
}


