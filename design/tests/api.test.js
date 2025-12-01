/**
 * Tests pour api.js - Classe CloudDiagnozeAPI
 */

// Mock de authManager
global.authManager = {
    getToken: jest.fn(() => 'mock-jwt-token'),
    clearAuth: jest.fn()
};

// Classe CloudDiagnozeAPI (copiée de api.js pour les tests)
class CloudDiagnozeAPI {
    constructor() {
        this.baseURL = API_CONFIG.BASE_URL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const token = authManager ? authManager.getToken() : null;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` }),
                    ...options.headers
                }
            });

            if (response.status === 401) {
                if (authManager) {
                    authManager.clearAuth();
                }
                window.location.href = 'login.html';
                throw new Error('Session expirée. Veuillez vous reconnecter.');
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    async getEC2Instances(params = {}) {
        const queryParams = new URLSearchParams({
            limit: params.limit || 100,
            latest_only: params.latest_only !== undefined ? params.latest_only : true,
            ...(params.region && { region: params.region }),
            ...(params.scan_id && { scan_id: params.scan_id })
        });

        return await this.request(`${API_CONFIG.ENDPOINTS.EC2_INSTANCES}?${queryParams}`);
    }

    async getS3Buckets(params = {}) {
        const queryParams = new URLSearchParams({
            limit: params.limit || 100,
            latest_only: params.latest_only !== undefined ? params.latest_only : true,
            ...(params.region && { region: params.region })
        });

        return await this.request(`${API_CONFIG.ENDPOINTS.S3_BUCKETS}?${queryParams}`);
    }

    async getScansHistory(params = {}) {
        const queryParams = new URLSearchParams({
            limit: params.limit || 100,
            ...(params.service_type && { service_type: params.service_type })
        });

        return await this.request(`${API_CONFIG.ENDPOINTS.SCANS_HISTORY}?${queryParams}`);
    }

    async getScanStatus(services) {
        const servicesParam = Array.isArray(services) ? services.join(',') : services;
        return await this.request(`${API_CONFIG.ENDPOINTS.SCAN_STATUS}?services=${servicesParam}`);
    }
}

describe('CloudDiagnozeAPI', () => {
    let api;

    beforeEach(() => {
        api = new CloudDiagnozeAPI();
        global.authManager.getToken.mockReturnValue('mock-jwt-token');
    });

    // ========================================
    // TESTS : Configuration de base
    // ========================================
    describe('Configuration', () => {
        test('baseURL est correctement définie', () => {
            expect(api.baseURL).toBe('http://localhost:8000/api/v1');
        });
    });

    // ========================================
    // TESTS : Méthode request()
    // ========================================
    describe('request()', () => {
        test('ajoute le header Authorization avec le token JWT', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ data: 'test' })
            });

            await api.request('/test-endpoint');

            expect(global.fetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/v1/test-endpoint',
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'Authorization': 'Bearer mock-jwt-token',
                        'Content-Type': 'application/json'
                    })
                })
            );
        });

        test('gère erreur 401 et redirige vers login', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: false,
                status: 401
            });

            await expect(api.request('/protected')).rejects.toThrow('Session expirée');
            expect(global.authManager.clearAuth).toHaveBeenCalled();
            expect(global.window.location.href).toBe('login.html');
        });

        test('gère les erreurs HTTP non-401', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: false,
                status: 500
            });

            await expect(api.request('/error')).rejects.toThrow('HTTP error! status: 500');
        });

        test('fonctionne sans token (authManager null)', async () => {
            const originalAuthManager = global.authManager;
            global.authManager = null;

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ data: 'public' })
            });

            // Recréer l'API pour tester sans authManager
            const apiNoAuth = new CloudDiagnozeAPI();
            const result = await apiNoAuth.request('/public');

            expect(result).toEqual({ data: 'public' });
            global.authManager = originalAuthManager;
        });
    });

    // ========================================
    // TESTS : Endpoints EC2
    // ========================================
    describe('getEC2Instances()', () => {
        test('construit l\'URL avec les paramètres par défaut', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ instances: [], total_instances: 0 })
            });

            await api.getEC2Instances();

            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/ec2/instances?'),
                expect.any(Object)
            );
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('limit=100'),
                expect.any(Object)
            );
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('latest_only=true'),
                expect.any(Object)
            );
        });

        test('accepte des paramètres personnalisés', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ instances: [], total_instances: 0 })
            });

            await api.getEC2Instances({ limit: 50, region: 'eu-west-1' });

            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('limit=50'),
                expect.any(Object)
            );
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('region=eu-west-1'),
                expect.any(Object)
            );
        });
    });

    // ========================================
    // TESTS : Endpoints S3
    // ========================================
    describe('getS3Buckets()', () => {
        test('construit l\'URL correctement', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ buckets: [], total_buckets: 0 })
            });

            await api.getS3Buckets();

            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/s3/buckets?'),
                expect.any(Object)
            );
        });
    });

    // ========================================
    // TESTS : Historique des scans
    // ========================================
    describe('getScansHistory()', () => {
        test('récupère l\'historique avec les paramètres', async () => {
            const mockScans = {
                scans: [
                    { scan_id: 1, service_type: 'ec2', status: 'success' },
                    { scan_id: 2, service_type: 's3', status: 'success' }
                ],
                total_scans: 2
            };

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockScans
            });

            const result = await api.getScansHistory({ limit: 20 });

            expect(result).toEqual(mockScans);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('limit=20'),
                expect.any(Object)
            );
        });
    });

    // ========================================
    // TESTS : Statut du scan
    // ========================================
    describe('getScanStatus()', () => {
        test('accepte un tableau de services', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ completed: true, services_status: {} })
            });

            await api.getScanStatus(['ec2', 's3', 'vpc']);

            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('services=ec2,s3,vpc'),
                expect.any(Object)
            );
        });

        test('accepte une string de services', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ completed: false, services_status: {} })
            });

            await api.getScanStatus('ec2');

            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('services=ec2'),
                expect.any(Object)
            );
        });
    });
});

