class GlobalStats {
    constructor() {
        this.ec2Instances = [];
        this.s3Buckets = [];
        this.scanRuns = [];
    }

    async loadAllData(options = {}) {
        try {
            const { scan_id } = options;

            if (scan_id) {
                await this.loadLatestSession(scan_id);
            } else {
                await this.loadLatestSession();
            }

            return {
                ec2: this.ec2Instances,
                s3: this.s3Buckets,
                scans: this.scanRuns
            };
        } catch (error) {
            console.error('❌ Erreur chargement données globales:', error);
            throw error;
        }
    }

    async loadLatestSession(scanId = null) {
        try {
            const session = await api.getLatestScanSession(scanId);

            console.log('📊 Session de scan chargée:', session);

            this.ec2Instances = [];
            this.s3Buckets = [];

            const scanIdByService = {};
            if (session.scans && session.scans.length > 0) {
                session.scans.forEach(scan => {
                    scanIdByService[scan.service_type] = scan.scan_id;
                });
            }

            const scannedServices = session.services || [];

            if (scannedServices.includes('ec2') && scanIdByService.ec2) {
                const ec2Data = await api.getEC2Instances({ limit: 100, scan_id: scanIdByService.ec2 });
                this.ec2Instances = ec2Data.instances || [];
                console.log(`✅ EC2: ${this.ec2Instances.length} instances chargées (scan #${scanIdByService.ec2})`);
            } else {
                console.log('⚪ EC2: Non scanné dans cette session');
            }

            if (scannedServices.includes('s3') && scanIdByService.s3) {
                const s3Data = await api.getS3Buckets({ limit: 100, scan_id: scanIdByService.s3 });
                this.s3Buckets = s3Data.buckets || [];
                console.log(`✅ S3: ${this.s3Buckets.length} buckets chargés (scan #${scanIdByService.s3})`);
            } else {
                console.log('⚪ S3: Non scanné dans cette session');
            }

            const scansData = await api.getScanRuns({ limit: 100 });
            this.scanRuns = scansData.scans || [];

            console.log(`✅ Session chargée: ${scannedServices.join(', ') || 'aucun service'} | Total: ${this.ec2Instances.length + this.s3Buckets.length} ressources`);
        } catch (error) {
            console.error('❌ Erreur chargement session:', error);
            throw error;
        }
    }

    async loadSpecificScan(scan_id) {
        try {
            console.log(`📊 Chargement du scan #${scan_id}...`);

            const queryParams = { limit: 100, scan_id };

            const ec2Data = await api.getEC2Instances(queryParams);
            this.ec2Instances = ec2Data.instances || [];

            const s3Data = await api.getS3Buckets(queryParams);
            this.s3Buckets = s3Data.buckets || [];

            const scansData = await api.getScanRuns({ limit: 100 });
            this.scanRuns = scansData.scans || [];

            console.log(`✅ Scan #${scan_id} chargé: ${this.ec2Instances.length} EC2, ${this.s3Buckets.length} S3`);
        } catch (error) {
            console.error(`❌ Erreur chargement scan #${scan_id}:`, error);
            throw error;
        }
    }

    getTotalResources() {
        return {
            total: this.ec2Instances.length + this.s3Buckets.length,
            ec2: this.ec2Instances.length,
            s3: this.s3Buckets.length
        };
    }

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

        return {
            total: alerts.length,
            danger: alerts.filter(a => a.type === 'danger').length,
            warning: alerts.filter(a => a.type === 'warning').length,
            info: alerts.filter(a => a.type === 'info').length,
            alerts: alerts
        };
    }

    getResourceDistribution() {
        const total = this.ec2Instances.length + this.s3Buckets.length;

        return {
            ec2: {
                count: this.ec2Instances.length,
                percentage: total > 0 ? Math.round((this.ec2Instances.length / total) * 100) : 0
            },
            s3: {
                count: this.s3Buckets.length,
                percentage: total > 0 ? Math.round((this.s3Buckets.length / total) * 100) : 0
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

    getAllResourcesList() {
        const resources = [];

        this.ec2Instances.forEach(instance => {
            resources.push({
                type: 'EC2',
                name: instance.tags?.Name || `Instance sans nom`,
                id: instance.instance_id,
                region: instance.region || 'N/A',
                state: instance.state || 'unknown',
                instanceType: instance.instance_type || 'N/A'
            });
        });

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

    /**
     * Calcule le Health Score de l'infrastructure (0-100)
     */
    getInfrastructureHealthScore() {
        const totalResources = this.ec2Instances.length + this.s3Buckets.length;

        if (totalResources === 0) {
            return {
                overall: 0,
                security: 0,
                performance: 0,
                cost: 0,
                compliance: 0,
                details: {
                    security: { score: 0, checks: [] },
                    performance: { score: 0, checks: [] },
                    cost: { score: 0, checks: [] },
                    compliance: { score: 0, checks: [] }
                }
            };
        }

        const securityChecks = [];
        let securityPoints = 0;
        let securityMax = 0;

        const s3Encrypted = this.s3Buckets.filter(b => b.encryption_enabled).length;
        const s3EncryptionScore = this.s3Buckets.length > 0 ? (s3Encrypted / this.s3Buckets.length) * 100 : 100;
        securityPoints += s3EncryptionScore;
        securityMax += 100;
        securityChecks.push({ name: 'S3 Encryption', score: s3EncryptionScore, passed: s3Encrypted, total: this.s3Buckets.length });

        const s3Private = this.s3Buckets.filter(b => b.public_access_blocked && !b.public_read_enabled).length;
        const s3PrivacyScore = this.s3Buckets.length > 0 ? (s3Private / this.s3Buckets.length) * 100 : 100;
        securityPoints += s3PrivacyScore;
        securityMax += 100;
        securityChecks.push({ name: 'S3 Private Access', score: s3PrivacyScore, passed: s3Private, total: this.s3Buckets.length });

        const securityScore = securityMax > 0 ? Math.round(securityPoints / securityMax * 100) : 0;

        const performanceChecks = [];
        let performancePoints = 0;
        let performanceMax = 0;

        const ec2HealthyCPU = this.ec2Instances.filter(i => !i.performance?.cpu_utilization_avg || i.performance.cpu_utilization_avg < 80).length;
        const ec2CPUScore = this.ec2Instances.length > 0 ? (ec2HealthyCPU / this.ec2Instances.length) * 100 : 100;
        performancePoints += ec2CPUScore;
        performanceMax += 100;
        performanceChecks.push({ name: 'EC2 CPU Health', score: ec2CPUScore, passed: ec2HealthyCPU, total: this.ec2Instances.length });

        const performanceScore = performanceMax > 0 ? Math.round(performancePoints / performanceMax * 100) : 0;

        const costChecks = [];
        let costPoints = 0;
        let costMax = 0;

        const ec2WithTags = this.ec2Instances.filter(i => i.tags && Object.keys(i.tags).length > 0).length;
        const ec2TagsScore = this.ec2Instances.length > 0 ? (ec2WithTags / this.ec2Instances.length) * 100 : 100;
        costPoints += ec2TagsScore;
        costMax += 100;
        costChecks.push({ name: 'EC2 Tagged', score: ec2TagsScore, passed: ec2WithTags, total: this.ec2Instances.length });

        const s3WithLifecycle = this.s3Buckets.filter(b => b.lifecycle_enabled).length;
        const s3LifecycleScore = this.s3Buckets.length > 0 ? (s3WithLifecycle / this.s3Buckets.length) * 100 : 100;
        costPoints += s3LifecycleScore;
        costMax += 100;
        costChecks.push({ name: 'S3 Lifecycle', score: s3LifecycleScore, passed: s3WithLifecycle, total: this.s3Buckets.length });

        const costScore = costMax > 0 ? Math.round(costPoints / costMax * 100) : 0;

        const complianceChecks = [];
        let compliancePoints = 0;
        let complianceMax = 0;

        const s3Versioned = this.s3Buckets.filter(b => b.versioning_enabled).length;
        const s3VersioningScore = this.s3Buckets.length > 0 ? (s3Versioned / this.s3Buckets.length) * 100 : 100;
        compliancePoints += s3VersioningScore;
        complianceMax += 100;
        complianceChecks.push({ name: 'S3 Versioning', score: s3VersioningScore, passed: s3Versioned, total: this.s3Buckets.length });

        const s3Logged = this.s3Buckets.filter(b => b.logging_enabled).length;
        const s3LoggingScore = this.s3Buckets.length > 0 ? (s3Logged / this.s3Buckets.length) * 100 : 100;
        compliancePoints += s3LoggingScore;
        complianceMax += 100;
        complianceChecks.push({ name: 'S3 Logging', score: s3LoggingScore, passed: s3Logged, total: this.s3Buckets.length });

        const complianceScore = complianceMax > 0 ? Math.round(compliancePoints / complianceMax * 100) : 0;

        const overallScore = Math.round((securityScore * 0.35 + performanceScore * 0.25 + costScore * 0.20 + complianceScore * 0.20));

        return {
            overall: overallScore,
            security: securityScore,
            performance: performanceScore,
            cost: costScore,
            compliance: complianceScore,
            details: {
                security: { score: securityScore, checks: securityChecks },
                performance: { score: performanceScore, checks: performanceChecks },
                cost: { score: costScore, checks: costChecks },
                compliance: { score: complianceScore, checks: complianceChecks }
            }
        };
    }
}

// Instance globale
const globalStats = new GlobalStats();

