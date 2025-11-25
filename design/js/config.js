/**
 * Configuration de l'API CloudDiagnoze
 */

const API_CONFIG = {
    // URL de base de l'API
    BASE_URL: 'http://localhost:8000/api/v1',
    
    // Endpoints disponibles
    ENDPOINTS: {
        LATEST_SCAN_SESSION: '/scans/latest-session',
        SCANS_HISTORY: '/scans/history',
        SCAN_STATUS: '/scans/status',
        EC2_INSTANCES: '/ec2/instances',
        EC2_INSTANCE_BY_ID: '/ec2/instances',
        S3_BUCKETS: '/s3/buckets',
        S3_BUCKET_BY_NAME: '/s3/buckets',
        VPC_INSTANCES: '/vpc/instances',
        RDS_INSTANCES: '/rds/instances',
        ADMIN_CLEAR_USER_DATA: '/admin/clear-user-data',
        ADMIN_CLEAR_DATABASE: '/admin/clear-database'
    },
    
    // Timeout pour les requêtes (en ms)
    TIMEOUT: 10000,
    
    // Client ID par défaut (à modifier selon tes besoins)
    DEFAULT_CLIENT_ID: 'ASM-Enterprise'
};

// Export pour utilisation dans d'autres fichiers
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API_CONFIG;
}

