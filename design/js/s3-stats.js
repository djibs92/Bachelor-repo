/**
 * Classe pour calculer les statistiques S3
 */
class S3Stats {
    constructor() {
        this.buckets = [];
    }

    /**
     * Charge les buckets depuis l'API
     */
    async loadBuckets() {
        try {
            // Vérifier si S3 a été scanné dans la dernière session
            const session = await api.getLatestScanSession();
            const scannedServices = session.services || [];

            if (!scannedServices.includes('s3')) {
                console.log('⚪ S3 non scanné dans la dernière session');
                this.buckets = [];
                return this.buckets;
            }

            // Récupérer le scan_id S3 de cette session
            const s3Scan = session.scans?.find(s => s.service_type === 's3');
            if (!s3Scan) {
                console.log('⚪ Aucun scan S3 trouvé dans la session');
                this.buckets = [];
                return this.buckets;
            }

            // S3 a été scanné, charger les données avec le scan_id spécifique
            const data = await api.getS3Buckets({ limit: 100, scan_id: s3Scan.scan_id });
            this.buckets = data.buckets || [];
            console.log(`✅ ${this.buckets.length} buckets S3 chargés (scan #${s3Scan.scan_id})`);
            return this.buckets;
        } catch (error) {
            console.error('❌ Erreur chargement buckets S3:', error);
            return [];
        }
    }

    /**
     * Statistiques globales des buckets
     */
    getTotalBucketsStats() {
        const total = this.buckets.length;
        const regions = [...new Set(this.buckets.map(b => b.region))];
        const totalRegions = regions.length;

        return {
            total,
            totalRegions,
            regions
        };
    }

    /**
     * Statistiques de sécurité - Encryption
     */
    getEncryptionStats() {
        const total = this.buckets.length;
        const encrypted = this.buckets.filter(b => b.encryption_enabled).length;
        const percentage = total > 0 ? Math.round((encrypted / total) * 100) : 0;

        return {
            encrypted,
            notEncrypted: total - encrypted,
            total,
            percentage
        };
    }

    /**
     * Statistiques de sécurité - Public Access
     */
    getPublicAccessStats() {
        const total = this.buckets.length;
        const blocked = this.buckets.filter(b => b.public_access_blocked).length;
        const publicRead = this.buckets.filter(b => b.public_read_enabled).length;
        const percentage = total > 0 ? Math.round((blocked / total) * 100) : 0;

        return {
            blocked,
            notBlocked: total - blocked,
            publicRead,
            total,
            percentage
        };
    }

    /**
     * Statistiques de sécurité - Versioning
     */
    getVersioningStats() {
        const total = this.buckets.length;
        const enabled = this.buckets.filter(b => b.versioning_enabled).length;
        const percentage = total > 0 ? Math.round((enabled / total) * 100) : 0;

        return {
            enabled,
            disabled: total - enabled,
            total,
            percentage
        };
    }

    /**
     * Statistiques d'activité - Requêtes (24h)
     */
    getRequestsStats() {
        let totalRequests = 0;
        let getRequests = 0;
        let putRequests = 0;
        let deleteRequests = 0;

        this.buckets.forEach(bucket => {
            if (bucket.performance) {
                totalRequests += bucket.performance.all_requests || 0;
                getRequests += bucket.performance.get_requests || 0;
                putRequests += bucket.performance.put_requests || 0;
                deleteRequests += bucket.performance.delete_requests || 0;
            }
        });

        return {
            total: totalRequests,
            get: getRequests,
            put: putRequests,
            delete: deleteRequests
        };
    }

    /**
     * Statistiques de transfert de données (24h)
     */
    getDataTransferStats() {
        let totalDownload = 0;
        let totalUpload = 0;

        this.buckets.forEach(bucket => {
            if (bucket.performance) {
                totalDownload += bucket.performance.bytes_downloaded || 0;
                totalUpload += bucket.performance.bytes_uploaded || 0;
            }
        });

        const total = totalDownload + totalUpload;

        return {
            total,
            download: totalDownload,
            upload: totalUpload,
            totalFormatted: this.formatBytes(total),
            downloadFormatted: this.formatBytes(totalDownload),
            uploadFormatted: this.formatBytes(totalUpload)
        };
    }

    /**
     * Répartition des buckets par région
     */
    getRegionDistribution() {
        const byRegion = {};

        this.buckets.forEach(bucket => {
            const region = bucket.region || 'unknown';
            byRegion[region] = (byRegion[region] || 0) + 1;
        });

        // Trier par nombre de buckets (décroissant)
        const sorted = Object.entries(byRegion)
            .sort((a, b) => b[1] - a[1]);

        return {
            byRegion,
            labels: sorted.map(([region]) => region),
            data: sorted.map(([, count]) => count)
        };
    }

    /**
     * État de sécurité (pour graphique stacked bar)
     */
    getSecurityStateDistribution() {
        const encryption = this.getEncryptionStats();
        const publicAccess = this.getPublicAccessStats();
        const versioning = this.getVersioningStats();
        const logging = this.buckets.filter(b => b.logging_enabled).length;

        return {
            labels: ['Encryption', 'Public Access Blocked', 'Versioning', 'Logging'],
            enabled: [
                encryption.encrypted,
                publicAccess.blocked,
                versioning.enabled,
                logging
            ],
            disabled: [
                encryption.notEncrypted,
                publicAccess.notBlocked,
                versioning.disabled,
                this.buckets.length - logging
            ]
        };
    }

    /**
     * Fonctionnalités avancées (pour graphique bar)
     */
    getAdvancedFeaturesDistribution() {
        const lifecycle = this.buckets.filter(b => b.lifecycle_enabled).length;
        const cors = this.buckets.filter(b => b.cors_enabled).length;
        const website = this.buckets.filter(b => b.website_enabled).length;
        const notifications = this.buckets.filter(b => b.notifications_enabled).length;
        const replication = this.buckets.filter(b => b.replication_enabled).length;

        return {
            labels: ['Lifecycle', 'CORS', 'Website', 'Notifications', 'Replication'],
            data: [lifecycle, cors, website, notifications, replication]
        };
    }

    /**
     * Activité par bucket (top 10)
     */
    getActivityByBucket() {
        // Filtrer les buckets avec activité
        const bucketsWithActivity = this.buckets
            .filter(b => b.performance && b.performance.all_requests > 0)
            .sort((a, b) => (b.performance.all_requests || 0) - (a.performance.all_requests || 0))
            .slice(0, 10);

        if (bucketsWithActivity.length === 0) {
            return {
                labels: [],
                get: [],
                put: [],
                delete: [],
                hasActivity: false
            };
        }

        return {
            labels: bucketsWithActivity.map(b => b.bucket_name),
            get: bucketsWithActivity.map(b => b.performance.get_requests || 0),
            put: bucketsWithActivity.map(b => b.performance.put_requests || 0),
            delete: bucketsWithActivity.map(b => b.performance.delete_requests || 0),
            hasActivity: true
        };
    }

    /**
     * Génère les alertes de sécurité
     */
    getAlerts() {
        const alerts = [];

        // Buckets non chiffrés
        const notEncrypted = this.buckets.filter(b => !b.encryption_enabled);
        if (notEncrypted.length > 0) {
            alerts.push({
                type: 'danger',
                icon: 'lock_open',
                title: 'Buckets non chiffrés',
                message: `${notEncrypted.length} bucket(s) sans chiffrement`,
                buckets: notEncrypted.map(b => b.bucket_name)
            });
        }

        // Buckets publics
        const publicBuckets = this.buckets.filter(b => !b.public_access_blocked || b.public_read_enabled);
        if (publicBuckets.length > 0) {
            alerts.push({
                type: 'danger',
                icon: 'public',
                title: 'Buckets avec accès public',
                message: `${publicBuckets.length} bucket(s) potentiellement publics`,
                buckets: publicBuckets.map(b => b.bucket_name)
            });
        }

        // Buckets sans versioning
        const noVersioning = this.buckets.filter(b => !b.versioning_enabled);
        if (noVersioning.length > 0) {
            alerts.push({
                type: 'warning',
                icon: 'history',
                title: 'Buckets sans versioning',
                message: `${noVersioning.length} bucket(s) sans versioning`,
                buckets: noVersioning.map(b => b.bucket_name)
            });
        }

        // Buckets sans logging
        const noLogging = this.buckets.filter(b => !b.logging_enabled);
        if (noLogging.length > 0) {
            alerts.push({
                type: 'warning',
                icon: 'description',
                title: 'Buckets sans logging',
                message: `${noLogging.length} bucket(s) sans logs`,
                buckets: noLogging.map(b => b.bucket_name)
            });
        }

        // Bonnes pratiques
        if (notEncrypted.length === 0) {
            alerts.push({
                type: 'success',
                icon: 'check_circle',
                title: 'Bonne pratique',
                message: 'Tous les buckets sont chiffrés'
            });
        }

        if (publicBuckets.length === 0) {
            alerts.push({
                type: 'success',
                icon: 'shield',
                title: 'Bonne pratique',
                message: 'Tous les buckets sont protégés contre l\'accès public'
            });
        }

        // Info sur l'activité
        const requestsStats = this.getRequestsStats();
        if (requestsStats.total === 0) {
            alerts.push({
                type: 'info',
                icon: 'info',
                title: 'Aucune activité récente',
                message: 'Aucune requête détectée sur les dernières 24h'
            });
        }

        return alerts;
    }

    /**
     * Formate les octets en unité lisible
     */
    formatBytes(bytes) {
        if (bytes === 0 || bytes === null || bytes === undefined) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }
}

// Instance globale
const s3Stats = new S3Stats();

