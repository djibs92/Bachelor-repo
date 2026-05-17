/**
 * Tests pour auth.js - Gestion de l'authentification (JWT via cookie httpOnly)
 *
 * Depuis la migration sécurité, le JWT n'est plus stocké dans localStorage.
 * Il est transporté dans un cookie httpOnly posé par le backend.
 * Seules les infos utilisateur non sensibles sont mises en cache côté JS.
 */

// Clés de stockage (copiées de auth.js)
const STORAGE_KEYS = {
    USER: 'clouddiagnoze_user'
};

// Classe AuthManager simplifiée pour les tests (mirroir de design/js/auth.js)
class AuthManager {
    constructor() {
        this.user = this.getUser();
    }

    // Conservée pour rétro-compatibilité, retourne toujours null
    getToken() {
        return null;
    }

    getUser() {
        const userJson = localStorage.getItem(STORAGE_KEYS.USER);
        return userJson ? JSON.parse(userJson) : null;
    }

    setAuth(_token, user) {
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
        this.user = user;
    }

    clearAuth() {
        localStorage.removeItem(STORAGE_KEYS.USER);
        this.user = null;
    }

    isAuthenticated() {
        return !!this.user;
    }

    async login(email, password) {
        try {
            const response = await fetch(`${AUTH_API_BASE_URL}/login`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Erreur lors de la connexion');
            }

            this.setAuth(null, data.user);
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
    // TESTS : Gestion du token (cookie httpOnly)
    // ========================================
    describe('Token Management', () => {
        test('getToken retourne toujours null (JWT en cookie httpOnly, inaccessible au JS)', () => {
            expect(authManager.getToken()).toBeNull();
        });

        test('le token JWT n\'est jamais écrit dans localStorage', () => {
            const user = { id: 1, email: 'test@example.com', full_name: 'Test User' };
            authManager.setAuth('jwt-test-token-123', user);

            // Seul l'objet utilisateur doit être stocké, jamais le token
            expect(localStorage.setItem).toHaveBeenCalledWith(STORAGE_KEYS.USER, JSON.stringify(user));
            expect(localStorage.setItem).not.toHaveBeenCalledWith(
                expect.stringMatching(/token/i),
                expect.anything()
            );
            expect(authManager.user).toEqual(user);
        });

        test('clearAuth supprime l\'utilisateur en cache (le cookie est effacé côté serveur)', () => {
            authManager.setAuth(null, { id: 1 });
            authManager.clearAuth();

            expect(localStorage.removeItem).toHaveBeenCalledWith(STORAGE_KEYS.USER);
            // Aucun appel pour retirer un token ne doit avoir eu lieu
            expect(localStorage.removeItem).not.toHaveBeenCalledWith(
                expect.stringMatching(/token/i)
            );
            expect(authManager.user).toBeNull();
        });
    });

    // ========================================
    // TESTS : Authentification
    // ========================================
    describe('isAuthenticated', () => {
        test('retourne false si pas d\'utilisateur en cache', () => {
            expect(authManager.isAuthenticated()).toBe(false);
        });

        test('retourne true si un utilisateur est en cache', () => {
            authManager.user = { id: 1, email: 'test@example.com' };
            expect(authManager.isAuthenticated()).toBe(true);
        });
    });



    // ========================================
    // TESTS : Login API
    // ========================================
    describe('login', () => {
        test('login réussi met en cache l\'utilisateur (token en cookie httpOnly) et envoie credentials: include', async () => {
            const mockResponse = {
                user: { id: 1, email: 'user@test.com', full_name: 'Test User' }
            };

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse
            });

            const result = await authManager.login('user@test.com', 'password123');

            expect(result.success).toBe(true);
            expect(result.user).toEqual(mockResponse.user);
            // Le token JWT n'est plus exposé au JS
            expect(authManager.getToken()).toBeNull();
            expect(authManager.user).toEqual(mockResponse.user);

            expect(global.fetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/v1/auth/login',
                expect.objectContaining({
                    method: 'POST',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: 'user@test.com', password: 'password123' })
                })
            );
            // Le token ne doit jamais être stocké dans localStorage
            expect(localStorage.setItem).not.toHaveBeenCalledWith(
                expect.stringMatching(/token/i),
                expect.anything()
            );
        });

        test('login échoué retourne erreur et ne met rien en cache', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: false,
                json: async () => ({ detail: 'Email ou mot de passe incorrect' })
            });

            const result = await authManager.login('wrong@test.com', 'wrongpass');

            expect(result.success).toBe(false);
            expect(result.error).toBe('Email ou mot de passe incorrect');
            expect(authManager.user).toBeNull();
            expect(authManager.getToken()).toBeNull();
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
