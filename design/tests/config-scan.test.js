/**
 * Tests pour config-scan.js - Configuration et lancement des scans
 */

// Classe ConfigScan simplifiée pour les tests
class ConfigScan {
    constructor() {
        this.selectedServices = [];
        this.selectedRegions = [];
        this.regionGroups = {
            'US East': ['us-east-1', 'us-east-2'],
            'US West': ['us-west-1', 'us-west-2'],
            'Europe': ['eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1'],
            'Asia Pacific': ['ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2'],
            'Other': ['sa-east-1', 'ca-central-1']
        };
        this.allRegions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2',
            'sa-east-1', 'ca-central-1'
        ];
        this.scannedServices = [];
    }

    toggleService(service) {
        const isSelected = this.selectedServices.includes(service);
        if (isSelected) {
            this.selectedServices = this.selectedServices.filter(s => s !== service);
        } else {
            if (!this.selectedServices.includes(service)) {
                this.selectedServices.push(service);
            }
        }
    }

    toggleRegion(region, checked) {
        if (checked) {
            if (!this.selectedRegions.includes(region)) {
                this.selectedRegions.push(region);
            }
        } else {
            this.selectedRegions = this.selectedRegions.filter(r => r !== region);
        }
    }

    toggleAllRegions(checked) {
        if (checked) {
            this.selectedRegions = [...this.allRegions];
        } else {
            this.selectedRegions = [];
        }
    }

    validateScanConfig() {
        if (this.selectedServices.length === 0) {
            return { valid: false, error: 'Veuillez sélectionner au moins un service' };
        }
        if (this.selectedRegions.length === 0) {
            return { valid: false, error: 'Veuillez sélectionner au moins une région' };
        }
        return { valid: true };
    }

    groupScansByTimestamp(scans) {
        const sorted = [...scans].sort((a, b) =>
            new Date(b.scan_timestamp) - new Date(a.scan_timestamp)
        );

        const groups = [];
        const timeThreshold = 60000; // 1 minute

        sorted.forEach(scan => {
            const scanTime = new Date(scan.scan_timestamp).getTime();
            let group = groups.find(g =>
                Math.abs(new Date(g.timestamp).getTime() - scanTime) < timeThreshold
            );

            if (!group) {
                group = {
                    id: scan.scan_id,
                    timestamp: scan.scan_timestamp,
                    scans: []
                };
                groups.push(group);
            }

            group.scans.push(scan);
        });

        return groups;
    }
}

describe('ConfigScan', () => {
    let configScan;

    beforeEach(() => {
        configScan = new ConfigScan();
    });

    // ========================================
    // TESTS : Sélection des services
    // ========================================
    describe('toggleService()', () => {
        test('ajoute un service non sélectionné', () => {
            configScan.toggleService('ec2');
            expect(configScan.selectedServices).toContain('ec2');
        });

        test('retire un service déjà sélectionné', () => {
            configScan.selectedServices = ['ec2', 's3'];
            configScan.toggleService('ec2');
            expect(configScan.selectedServices).not.toContain('ec2');
            expect(configScan.selectedServices).toContain('s3');
        });

        test('ne crée pas de doublons', () => {
            configScan.toggleService('vpc');
            configScan.toggleService('rds');
            configScan.toggleService('vpc'); // Toggle off
            configScan.toggleService('vpc'); // Toggle on again
            
            const vpcCount = configScan.selectedServices.filter(s => s === 'vpc').length;
            expect(vpcCount).toBe(1);
        });

        test('gère tous les services AWS supportés', () => {
            const services = ['ec2', 's3', 'vpc', 'rds'];
            services.forEach(s => configScan.toggleService(s));
            
            expect(configScan.selectedServices).toHaveLength(4);
            expect(configScan.selectedServices).toEqual(expect.arrayContaining(services));
        });
    });

    // ========================================
    // TESTS : Sélection des régions
    // ========================================
    describe('toggleRegion()', () => {
        test('ajoute une région quand checked=true', () => {
            configScan.toggleRegion('eu-west-1', true);
            expect(configScan.selectedRegions).toContain('eu-west-1');
        });

        test('retire une région quand checked=false', () => {
            configScan.selectedRegions = ['eu-west-1', 'eu-west-2'];
            configScan.toggleRegion('eu-west-1', false);
            expect(configScan.selectedRegions).not.toContain('eu-west-1');
        });

        test('ne duplique pas les régions', () => {
            configScan.toggleRegion('us-east-1', true);
            configScan.toggleRegion('us-east-1', true);

            const count = configScan.selectedRegions.filter(r => r === 'us-east-1').length;
            expect(count).toBe(1);
        });
    });

    // ========================================
    // TESTS : Toutes les régions
    // ========================================
    describe('toggleAllRegions()', () => {
        test('sélectionne toutes les régions quand checked=true', () => {
            configScan.toggleAllRegions(true);
            expect(configScan.selectedRegions).toHaveLength(14);
            expect(configScan.selectedRegions).toContain('eu-west-1');
            expect(configScan.selectedRegions).toContain('us-east-1');
            expect(configScan.selectedRegions).toContain('ap-northeast-1');
        });

        test('désélectionne toutes les régions quand checked=false', () => {
            configScan.selectedRegions = ['eu-west-1', 'us-east-1'];
            configScan.toggleAllRegions(false);
            expect(configScan.selectedRegions).toHaveLength(0);
        });
    });

    // ========================================
    // TESTS : Validation de la configuration
    // ========================================
    describe('validateScanConfig()', () => {
        test('échoue si aucun service sélectionné', () => {
            configScan.selectedRegions = ['eu-west-1'];
            const result = configScan.validateScanConfig();
            expect(result.valid).toBe(false);
            expect(result.error).toContain('service');
        });

        test('échoue si aucune région sélectionnée', () => {
            configScan.selectedServices = ['ec2'];
            const result = configScan.validateScanConfig();
            expect(result.valid).toBe(false);
            expect(result.error).toContain('région');
        });

        test('réussit avec services et régions sélectionnés', () => {
            configScan.selectedServices = ['ec2', 's3'];
            configScan.selectedRegions = ['eu-west-1', 'eu-west-2'];
            const result = configScan.validateScanConfig();
            expect(result.valid).toBe(true);
        });
    });

    // ========================================
    // TESTS : Groupement des scans par timestamp
    // ========================================
    describe('groupScansByTimestamp()', () => {
        test('groupe les scans avec timestamps proches', () => {
            const baseTime = new Date('2024-01-15T10:00:00Z');
            const scans = [
                { scan_id: 1, service_type: 'ec2', scan_timestamp: baseTime.toISOString() },
                { scan_id: 2, service_type: 's3', scan_timestamp: new Date(baseTime.getTime() + 5000).toISOString() }, // +5 sec
                { scan_id: 3, service_type: 'vpc', scan_timestamp: new Date(baseTime.getTime() + 10000).toISOString() } // +10 sec
            ];

            const groups = configScan.groupScansByTimestamp(scans);

            // Tous les 3 scans devraient être dans le même groupe (< 1 minute d'écart)
            expect(groups).toHaveLength(1);
            expect(groups[0].scans).toHaveLength(3);
        });

        test('sépare les scans avec timestamps éloignés', () => {
            const scans = [
                { scan_id: 1, service_type: 'ec2', scan_timestamp: '2024-01-15T10:00:00Z' },
                { scan_id: 2, service_type: 's3', scan_timestamp: '2024-01-15T10:05:00Z' }, // +5 min
                { scan_id: 3, service_type: 'vpc', scan_timestamp: '2024-01-15T11:00:00Z' }  // +1 heure
            ];

            const groups = configScan.groupScansByTimestamp(scans);

            // 3 groupes séparés (> 1 minute d'écart entre chaque)
            expect(groups).toHaveLength(3);
        });

        test('trie les groupes par timestamp décroissant', () => {
            const scans = [
                { scan_id: 1, service_type: 'ec2', scan_timestamp: '2024-01-15T08:00:00Z' },
                { scan_id: 2, service_type: 's3', scan_timestamp: '2024-01-15T12:00:00Z' },
                { scan_id: 3, service_type: 'vpc', scan_timestamp: '2024-01-15T10:00:00Z' }
            ];

            const groups = configScan.groupScansByTimestamp(scans);

            // Le plus récent en premier (12:00, 10:00, 08:00)
            expect(groups[0].scans[0].scan_timestamp).toBe('2024-01-15T12:00:00Z');
        });
    });

    // ========================================
    // TESTS : Groupes de régions
    // ========================================
    describe('Region Groups', () => {
        test('contient les groupes géographiques attendus', () => {
            expect(configScan.regionGroups).toHaveProperty('US East');
            expect(configScan.regionGroups).toHaveProperty('US West');
            expect(configScan.regionGroups).toHaveProperty('Europe');
            expect(configScan.regionGroups).toHaveProperty('Asia Pacific');
        });

        test('Europe contient les bonnes régions', () => {
            const europeRegions = configScan.regionGroups['Europe'];
            expect(europeRegions).toContain('eu-west-1');
            expect(europeRegions).toContain('eu-west-2');
            expect(europeRegions).toContain('eu-west-3');
            expect(europeRegions).toContain('eu-central-1');
        });

        test('allRegions contient toutes les régions des groupes', () => {
            const allGroupRegions = Object.values(configScan.regionGroups).flat();
            expect(configScan.allRegions).toHaveLength(allGroupRegions.length);
            allGroupRegions.forEach(region => {
                expect(configScan.allRegions).toContain(region);
            });
        });
    });
});

