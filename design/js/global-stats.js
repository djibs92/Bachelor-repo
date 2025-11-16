/**
 * Classe pour calculer les statistiques globales (EC2 + S3)
 */
class GlobalStats {
    constructor() {
        this.ec2Instances = [];
        this.s3Buckets = [];
        this.vpcInstances = [];
        this.scanRuns = [];
    }

    /**
     * Charge toutes les données (EC2 + S3 + VPC + Scans)
     */
    async loadAllData(options = {}) {
        try {
            const { scan_id } = options;

            // Paramètres de requête
            const queryParams = {
                limit: 100,
                latest_only: !scan_id, // Si scan_id est fourni, on ne veut pas latest_only
                ...(scan_id && { scan_id })
            };

            // Charger les instances EC2
            const ec2Data = await api.getEC2Instances(queryParams);
            this.ec2Instances = ec2Data.instances || [];

            // Charger les buckets S3
            const s3Data = await api.getS3Buckets(queryParams);
            this.s3Buckets = s3Data.buckets || [];

            // Charger les VPCs
            const vpcData = await api.getVPCInstances(queryParams);
            this.vpcInstances = vpcData.vpcs || [];

            // Charger l'historique des scans
            const scansData = await api.getScanRuns({ limit: 100 });
            this.scanRuns = scansData.scans || [];

            if (scan_id) {
                console.log(`✅ Données du scan #${scan_id} chargées: ${this.ec2Instances.length} EC2, ${this.s3Buckets.length} S3, ${this.vpcInstances.length} VPC`);
            } else {
                console.log(`✅ Données chargées: ${this.ec2Instances.length} EC2, ${this.s3Buckets.length} S3, ${this.vpcInstances.length} VPC, ${this.scanRuns.length} scans`);
            }

            return {
                ec2: this.ec2Instances,
                s3: this.s3Buckets,
                vpc: this.vpcInstances,
                scans: this.scanRuns
            };
        } catch (error) {
            console.error('❌ Erreur chargement données globales:', error);
            throw error;
        }
    }

    /**
     * Statistiques: Total des ressources
     */
    getTotalResources() {
        return {
            total: this.ec2Instances.length + this.s3Buckets.length + this.vpcInstances.length,
            ec2: this.ec2Instances.length,
            s3: this.s3Buckets.length,
            vpc: this.vpcInstances.length
        };
    }

    /**
     * Statistiques: Scans ce mois-ci
     */
    getScansThisMonth() {
        const now = new Date();
        const firstDayOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);

        const scansThisMonth = this.scanRuns.filter(scan => {
            const scanDate = new Date(scan.scan_timestamp);
            return scanDate >= firstDayOfMonth;
        });

        return {
            total: scansThisMonth.length,
            ec2: scansThisMonth.filter(s => s.service_type === 'ec2').length,
            s3: scansThisMonth.filter(s => s.service_type === 's3').length,
            vpc: scansThisMonth.filter(s => s.service_type === 'vpc').length,
            scans: scansThisMonth
        };
    }

    /**
     * Statistiques: Alertes actives (basées sur EC2 + S3)
     */
    getActiveAlerts() {
        const alerts = [];

        // Alertes EC2
        this.ec2Instances.forEach(instance => {
            // Instance sans IP publique
            if (!instance.public_ip) {
                alerts.push({
                    type: 'warning',
                    service: 'EC2',
                    resource: instance.instance_id,
                    message: 'Instance sans IP publique'
                });
            }

            // CPU élevé
            if (instance.performance?.cpu_utilization_avg > 80) {
                alerts.push({
                    type: 'danger',
                    service: 'EC2',
                    resource: instance.instance_id,
                    message: `CPU élevé: ${instance.performance.cpu_utilization_avg.toFixed(1)}%`
                });
            }

            // Instance sans tags
            if (!instance.tags || Object.keys(instance.tags).length === 0) {
                alerts.push({
                    type: 'info',
                    service: 'EC2',
                    resource: instance.instance_id,
                    message: 'Instance sans tags'
                });
            }
        });

        // Alertes S3
        this.s3Buckets.forEach(bucket => {
            // Bucket non chiffré
            if (!bucket.encryption_enabled) {
                alerts.push({
                    type: 'danger',
                    service: 'S3',
                    resource: bucket.bucket_name,
                    message: 'Bucket non chiffré'
                });
            }

            // Bucket public
            if (!bucket.public_access_blocked || bucket.public_read_enabled) {
                alerts.push({
                    type: 'danger',
                    service: 'S3',
                    resource: bucket.bucket_name,
                    message: 'Bucket potentiellement public'
                });
            }

            // Sans versioning
            if (!bucket.versioning_enabled) {
                alerts.push({
                    type: 'warning',
                    service: 'S3',
                    resource: bucket.bucket_name,
                    message: 'Versioning désactivé'
                });
            }

            // Sans logging
            if (!bucket.logging_enabled) {
                alerts.push({
                    type: 'info',
                    service: 'S3',
                    resource: bucket.bucket_name,
                    message: 'Logging désactivé'
                });
            }
        });

        // Alertes VPC
        this.vpcInstances.forEach(vpc => {
            const vpcName = vpc.tags?.Name || vpc.vpc_id;

            // Flow Logs désactivé
            if (!vpc.flow_logs_enabled) {
                alerts.push({
                    type: 'danger',
                    service: 'VPC',
                    resource: vpcName,
                    message: 'Flow Logs désactivé'
                });
            }

            // Pas d'Internet Gateway
            if (!vpc.internet_gateway_attached) {
                alerts.push({
                    type: 'warning',
                    service: 'VPC',
                    resource: vpcName,
                    message: 'Pas d\'Internet Gateway attaché'
                });
            }

            // VPC sans tags
            if (!vpc.tags || (typeof vpc.tags === 'object' ? Object.keys(vpc.tags).length === 0 : vpc.tags.length === 0)) {
                alerts.push({
                    type: 'info',
                    service: 'VPC',
                    resource: vpcName,
                    message: 'VPC sans tags'
                });
            }

            // Trop de subnets publics (> 50% des subnets)
            const totalSubnets = vpc.subnet_count || 0;
            const publicSubnets = vpc.public_subnets_count || 0;
            if (totalSubnets > 0 && (publicSubnets / totalSubnets) > 0.5) {
                alerts.push({
                    type: 'warning',
                    service: 'VPC',
                    resource: vpcName,
                    message: `Trop de subnets publics: ${publicSubnets}/${totalSubnets}`
                });
            }
        });

        return {
            total: alerts.length,
            danger: alerts.filter(a => a.type === 'danger').length,
            warning: alerts.filter(a => a.type === 'warning').length,
            info: alerts.filter(a => a.type === 'info').length,
            alerts: alerts
        };
    }

    /**
     * Répartition des ressources par type
     */
    getResourceDistribution() {
        const total = this.ec2Instances.length + this.s3Buckets.length + this.vpcInstances.length;

        return {
            ec2: {
                count: this.ec2Instances.length,
                percentage: total > 0 ? Math.round((this.ec2Instances.length / total) * 100) : 0
            },
            s3: {
                count: this.s3Buckets.length,
                percentage: total > 0 ? Math.round((this.s3Buckets.length / total) * 100) : 0
            },
            vpc: {
                count: this.vpcInstances.length,
                percentage: total > 0 ? Math.round((this.vpcInstances.length / total) * 100) : 0
            },
            total: total
        };
    }

    /**
     * CPU moyen global (EC2 uniquement)
     */
    getGlobalCPU() {
        if (this.ec2Instances.length === 0) {
            return { average: 0, instances: 0 };
        }

        const cpuValues = this.ec2Instances
            .filter(i => i.performance?.cpu_utilization_avg != null)
            .map(i => i.performance.cpu_utilization_avg);

        if (cpuValues.length === 0) {
            return { average: 0, instances: 0 };
        }

        const average = cpuValues.reduce((sum, val) => sum + val, 0) / cpuValues.length;

        return {
            average: Math.round(average * 10) / 10,
            instances: cpuValues.length,
            min: Math.min(...cpuValues),
            max: Math.max(...cpuValues)
        };
    }

    /**
     * Répartition des instances EC2 par état
     */
    getEC2StateDistribution() {
        const states = {};
        
        this.ec2Instances.forEach(instance => {
            const state = instance.state || 'unknown';
            states[state] = (states[state] || 0) + 1;
        });

        return {
            states: states,
            labels: Object.keys(states),
            data: Object.values(states)
        };
    }

    /**
     * Répartition des buckets S3 par région
     */
    getS3RegionDistribution() {
        const regions = {};

        this.s3Buckets.forEach(bucket => {
            const region = bucket.region || 'unknown';
            regions[region] = (regions[region] || 0) + 1;
        });

        return {
            regions: regions,
            labels: Object.keys(regions),
            data: Object.values(regions)
        };
    }

    /**
     * Répartition des instances EC2 par région
     */
    getEC2RegionDistribution() {
        const regions = {};

        this.ec2Instances.forEach(instance => {
            const region = instance.region || 'unknown';
            regions[region] = (regions[region] || 0) + 1;
        });

        return {
            regions: regions,
            labels: Object.keys(regions),
            data: Object.values(regions)
        };
    }

    /**
     * Répartition des VPCs par région
     */
    getVPCRegionDistribution() {
        const regions = {};

        this.vpcInstances.forEach(vpc => {
            const region = vpc.region || 'unknown';
            regions[region] = (regions[region] || 0) + 1;
        });

        return {
            regions: regions,
            labels: Object.keys(regions),
            data: Object.values(regions)
        };
    }

    /**
     * Retourne la liste complète de toutes les ressources (EC2 + S3)
     */
    getAllResourcesList() {
        const resources = [];

        // Ajouter les instances EC2
        this.ec2Instances.forEach(instance => {
            resources.push({
                type: 'EC2',
                name: instance.name || instance.instance_id,
                id: instance.instance_id,
                region: instance.region || 'N/A',
                state: instance.state || 'unknown',
                instanceType: instance.instance_type || 'N/A'
            });
        });

        // Ajouter les buckets S3
        this.s3Buckets.forEach(bucket => {
            resources.push({
                type: 'S3',
                name: bucket.bucket_name,
                id: bucket.bucket_name,
                region: bucket.region || 'N/A',
                state: 'active',
                instanceType: 'Bucket'
            });
        });

        return resources;
    }

    /**
     * Score de sécurité global (0-100)
     */
    getSecurityScore() {
        let totalChecks = 0;
        let passedChecks = 0;

        // Checks EC2
        this.ec2Instances.forEach(instance => {
            totalChecks += 2; // IP publique + Tags
            if (instance.public_ip) passedChecks++;
            if (instance.tags && Object.keys(instance.tags).length > 0) passedChecks++;
        });

        // Checks S3
        this.s3Buckets.forEach(bucket => {
            totalChecks += 4; // Encryption + Public Access + Versioning + Logging
            if (bucket.encryption_enabled) passedChecks++;
            if (bucket.public_access_blocked && !bucket.public_read_enabled) passedChecks++;
            if (bucket.versioning_enabled) passedChecks++;
            if (bucket.logging_enabled) passedChecks++;
        });

        // Checks VPC
        this.vpcInstances.forEach(vpc => {
            totalChecks += 3; // Flow Logs + Internet Gateway + Tags
            if (vpc.flow_logs_enabled) passedChecks++;
            if (vpc.internet_gateway_attached) passedChecks++;
            if (vpc.tags && (typeof vpc.tags === 'object' ? Object.keys(vpc.tags).length > 0 : vpc.tags.length > 0)) passedChecks++;
        });

        const score = totalChecks > 0 ? Math.round((passedChecks / totalChecks) * 100) : 0;

        return {
            score: score,
            totalChecks: totalChecks,
            passedChecks: passedChecks,
            failedChecks: totalChecks - passedChecks
        };
    }

    /**
     * Alertes critiques récentes - TOUTES les alertes danger + warning
     */
    getRecentCriticalAlerts() {
        const allAlerts = this.getActiveAlerts().alerts;

        // Filtrer les alertes critiques et warnings (pas de limite)
        const criticalAlerts = allAlerts.filter(a => a.type === 'danger' || a.type === 'warning');

        // Retourner TOUTES les alertes critiques
        return criticalAlerts;
    }

    /**
     * Historique des scans (derniers 30 jours)
     */
    getScanHistory() {
        const now = new Date();
        const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

        const recentScans = this.scanRuns.filter(scan => {
            const scanDate = new Date(scan.scan_timestamp);
            return scanDate >= thirtyDaysAgo;
        });

        // Grouper par jour
        const scansByDay = {};
        recentScans.forEach(scan => {
            const date = new Date(scan.scan_timestamp).toLocaleDateString('fr-FR');
            scansByDay[date] = (scansByDay[date] || 0) + 1;
        });

        return {
            total: recentScans.length,
            byDay: scansByDay,
            labels: Object.keys(scansByDay),
            data: Object.values(scansByDay)
        };
    }
}

// Instance globale
const globalStats = new GlobalStats();

