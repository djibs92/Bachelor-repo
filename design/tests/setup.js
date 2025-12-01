/**
 * Setup pour les tests Jest - CloudDiagnoze Frontend
 */

// Mock de localStorage
const localStorageMock = {
    store: {},
    getItem: jest.fn((key) => localStorageMock.store[key] || null),
    setItem: jest.fn((key, value) => {
        localStorageMock.store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
        delete localStorageMock.store[key];
    }),
    clear: jest.fn(() => {
        localStorageMock.store = {};
    })
};

Object.defineProperty(global, 'localStorage', {
    value: localStorageMock
});

// Mock de fetch
global.fetch = jest.fn();

// Mock de window.location
delete global.window.location;
global.window.location = {
    href: '',
    hostname: 'localhost',
    origin: 'http://localhost'
};

// Mock de console pour éviter le bruit dans les tests
global.console = {
    ...console,
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn()
};

// Configuration API globale (simulant config.env.js et config.js)
global.API_CONFIG = {
    BASE_URL: 'http://localhost:8000/api/v1',
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
    TIMEOUT: 10000,
    DEFAULT_CLIENT_ID: 'ASM-Enterprise'
};

global.AUTH_API_BASE_URL = 'http://localhost:8000/api/v1/auth';

// Reset des mocks avant chaque test
beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.store = {};
    global.fetch.mockClear();
    global.window.location.href = '';
});

