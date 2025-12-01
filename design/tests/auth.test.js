/**
 * Tests pour auth.js - Gestion de l'authentification
 */

// Clés de stockage (copiées de auth.js)
const STORAGE_KEYS = {
    TOKEN: 'clouddiagnoze_token',
    USER: 'clouddiagnoze_user'
};

// Classe AuthManager simplifiée pour les tests
class AuthManager {
    constructor() {
        this.token = this.getToken();
        this.user = this.getUser();
    }

    getToken() {
        return localStorage.getItem(STORAGE_KEYS.TOKEN);
    }

    getUser() {
        const userJson = localStorage.getItem(STORAGE_KEYS.USER);
        return userJson ? JSON.parse(userJson) : null;
    }

    setAuth(token, user) {
        localStorage.setItem(STORAGE_KEYS.TOKEN, token);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
        this.token = token;
        this.user = user;
    }

    clearAuth() {
        localStorage.removeItem(STORAGE_KEYS.TOKEN);
        localStorage.removeItem(STORAGE_KEYS.USER);
        this.token = null;
        this.user = null;
    }

    isAuthenticated() {
        return !!this.token;
    }

    async login(email, password) {
        try {
            const response = await fetch(`${AUTH_API_BASE_URL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Erreur lors de la connexion');
            }

            this.setAuth(data.access_token, data.user);
            return { success: true, user: data.user };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async signup(email, password, fullName = null, companyName = null, roleArn = null) {
        try {
            const response = await fetch(`${AUTH_API_BASE_URL}/signup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    password,
                    full_name: fullName,
                    company_name: companyName,
                    role_arn: roleArn
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Erreur lors de l\'inscription');
            }

            return { success: true, message: data.message };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

describe('AuthManager', () => {
    let authManager;

    beforeEach(() => {
        authManager = new AuthManager();
    });

    // ========================================
    // TESTS : Gestion du token
    // ========================================
    describe('Token Management', () => {
        test('getToken retourne null si aucun token stocké', () => {
            expect(authManager.getToken()).toBeNull();
        });

        test('setAuth stocke le token et l\'utilisateur', () => {
            const token = 'jwt-test-token-123';
            const user = { id: 1, email: 'test@example.com', full_name: 'Test User' };

            authManager.setAuth(token, user);

            expect(localStorage.setItem).toHaveBeenCalledWith(STORAGE_KEYS.TOKEN, token);
            expect(localStorage.setItem).toHaveBeenCalledWith(STORAGE_KEYS.USER, JSON.stringify(user));
            expect(authManager.token).toBe(token);
            expect(authManager.user).toEqual(user);
        });

        test('clearAuth supprime le token et l\'utilisateur', () => {
            authManager.setAuth('token', { id: 1 });
            authManager.clearAuth();

            expect(localStorage.removeItem).toHaveBeenCalledWith(STORAGE_KEYS.TOKEN);
            expect(localStorage.removeItem).toHaveBeenCalledWith(STORAGE_KEYS.USER);
            expect(authManager.token).toBeNull();
            expect(authManager.user).toBeNull();
        });
    });

    // ========================================
    // TESTS : Authentification
    // ========================================
    describe('isAuthenticated', () => {
        test('retourne false si pas de token', () => {
            expect(authManager.isAuthenticated()).toBe(false);
        });

        test('retourne true si token présent', () => {
            authManager.token = 'valid-token';
            expect(authManager.isAuthenticated()).toBe(true);
        });
    });

    // ========================================
    // TESTS : Login API
    // ========================================
    describe('login', () => {
        test('login réussi stocke le token et retourne success', async () => {
            const mockResponse = {
                access_token: 'jwt-token-abc123',
                user: { id: 1, email: 'user@test.com', full_name: 'Test User' }
            };

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse
            });

            const result = await authManager.login('user@test.com', 'password123');

            expect(result.success).toBe(true);
            expect(result.user).toEqual(mockResponse.user);
            expect(authManager.token).toBe(mockResponse.access_token);
            expect(global.fetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/v1/auth/login',
                expect.objectContaining({
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: 'user@test.com', password: 'password123' })
                })
            );
        });

        test('login échoué retourne erreur', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: false,
                json: async () => ({ detail: 'Email ou mot de passe incorrect' })
            });

            const result = await authManager.login('wrong@test.com', 'wrongpass');

            expect(result.success).toBe(false);
            expect(result.error).toBe('Email ou mot de passe incorrect');
            expect(authManager.token).toBeNull();
        });

        test('login gère les erreurs réseau', async () => {
            global.fetch.mockRejectedValueOnce(new Error('Network error'));

            const result = await authManager.login('user@test.com', 'password');

            expect(result.success).toBe(false);
            expect(result.error).toBe('Network error');
        });
    });

    // ========================================
    // TESTS : Signup API
    // ========================================
    describe('signup', () => {
        test('signup réussi retourne success', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ message: 'Compte créé avec succès' })
            });

            const result = await authManager.signup(
                'new@test.com',
                'StrongPass123',
                'New User',
                'Test Company',
                'arn:aws:iam::123456789:role/TestRole'
            );

            expect(result.success).toBe(true);
            expect(result.message).toBe('Compte créé avec succès');
            expect(global.fetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/v1/auth/signup',
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify({
                        email: 'new@test.com',
                        password: 'StrongPass123',
                        full_name: 'New User',
                        company_name: 'Test Company',
                        role_arn: 'arn:aws:iam::123456789:role/TestRole'
                    })
                })
            );
        });

        test('signup avec email existant retourne erreur', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: false,
                json: async () => ({ detail: 'Cet email est déjà utilisé' })
            });

            const result = await authManager.signup('existing@test.com', 'Pass123');

            expect(result.success).toBe(false);
            expect(result.error).toBe('Cet email est déjà utilisé');
        });
    });
});

