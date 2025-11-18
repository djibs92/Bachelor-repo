/**
 * Classe pour calculer les statistiques des VPCs
 */

class VPCStats {
    constructor() {
        this.vpcs = [];
        this.scanId = null;
        this.scanTimestamp = null;
    }

    /**
     * Charge les VPCs depuis l'API
     */
    async loadVPCs(params = {}) {
        try {
            // Vérifier si VPC a été scanné dans la dernière session
            const session = await api.getLatestScanSession();
            const scannedServices = session.services || [];

            if (!scannedServices.includes('vpc')) {
                console.log('⚪ VPC non scanné dans la dernière session');
                this.vpcs = [];
                this.scanId = null;
                this.scanTimestamp = null;
                return this.vpcs;
            }

            // Récupérer le scan_id VPC de cette session
            const vpcScan = session.scans?.find(s => s.service_type === 'vpc');
            if (!vpcScan) {
                console.log('⚪ Aucun scan VPC trouvé dans la session');
                this.vpcs = [];
                this.scanId = null;
                this.scanTimestamp = null;
                return this.vpcs;
            }

            // VPC a été scanné, charger les données avec le scan_id spécifique
            console.log('📡 Appel API getVPCInstances avec scan_id:', vpcScan.scan_id);
            const data = await api.getVPCInstances({ ...params, limit: 100, scan_id: vpcScan.scan_id });
            console.log('📦 Données reçues de l\'API:', data);
            this.vpcs = data.vpcs || [];
            this.scanId = data.scan_id;
            this.scanTimestamp = data.scan_timestamp;
            console.log(`✅ ${this.vpcs.length} VPCs chargés (scan #${vpcScan.scan_id})`);
            return this.vpcs;
        } catch (error) {
            console.error('❌ Erreur lors du chargement des VPCs:', error);
            throw error;
        }
    }

    /**
     * Statistiques totales des VPCs
     */
    getTotalVPCsStats() {
        const total = this.vpcs.length;
        const defaultVPCs = this.vpcs.filter(vpc => vpc.is_default).length;
        const customVPCs = total - defaultVPCs;
        
        // Calculer le nombre total de subnets
        const totalSubnets = this.vpcs.reduce((sum, vpc) => sum + (vpc.subnet_count || 0), 0);
        const publicSubnets = this.vpcs.reduce((sum, vpc) => sum + (vpc.public_subnets_count || 0), 0);
        const privateSubnets = this.vpcs.reduce((sum, vpc) => sum + (vpc.private_subnets_count || 0), 0);

        return {
            total,
            defaultVPCs,
            customVPCs,
            totalSubnets,
            publicSubnets,
            privateSubnets
        };
    }

    /**
     * Statistiques par région
     */
    getRegionsStats() {
        const regionMap = {};
        
        this.vpcs.forEach(vpc => {
            const region = vpc.region || 'unknown';
            if (!regionMap[region]) {
                regionMap[region] = {
                    count: 0,
                    subnets: 0,
                    vpcs: []
                };
            }
            regionMap[region].count++;
            regionMap[region].subnets += vpc.subnet_count || 0;
            regionMap[region].vpcs.push(vpc);
        });

        return regionMap;
    }

    /**
     * Distribution des subnets (public vs privé)
     */
    getSubnetDistribution() {
        const publicSubnets = this.vpcs.reduce((sum, vpc) => sum + (vpc.public_subnets_count || 0), 0);
        const privateSubnets = this.vpcs.reduce((sum, vpc) => sum + (vpc.private_subnets_count || 0), 0);

        return {
            public: publicSubnets,
            private: privateSubnets,
            total: publicSubnets + privateSubnets
        };
    }

    /**
     * Statistiques de sécurité
     */
    getSecurityStats() {
        const vpcsWithFlowLogs = this.vpcs.filter(vpc => vpc.flow_logs_enabled).length;
        const vpcsWithoutFlowLogs = this.vpcs.length - vpcsWithFlowLogs;
        
        const totalSecurityGroups = this.vpcs.reduce((sum, vpc) => sum + (vpc.security_groups_count || 0), 0);
        const totalNACLs = this.vpcs.reduce((sum, vpc) => sum + (vpc.network_acls_count || 0), 0);
        
        // Score de sécurité (0-100)
        const flowLogsScore = this.vpcs.length > 0 ? (vpcsWithFlowLogs / this.vpcs.length) * 100 : 0;

        return {
            vpcsWithFlowLogs,
            vpcsWithoutFlowLogs,
            totalSecurityGroups,
            totalNACLs,
            securityScore: Math.round(flowLogsScore)
        };
    }

    /**
     * Statistiques de connectivité
     */
    getConnectivityStats() {
        const vpcsWithIGW = this.vpcs.filter(vpc => vpc.internet_gateway_attached).length;
        const totalNATGateways = this.vpcs.reduce((sum, vpc) => sum + (vpc.nat_gateways_count || 0), 0);
        const totalVPCEndpoints = this.vpcs.reduce((sum, vpc) => sum + (vpc.vpc_endpoints_count || 0), 0);
        const totalPeeringConnections = this.vpcs.reduce((sum, vpc) => sum + (vpc.vpc_peering_connections_count || 0), 0);
        const totalTransitGatewayAttachments = this.vpcs.reduce((sum, vpc) => sum + (vpc.transit_gateway_attachments_count || 0), 0);

        return {
            vpcsWithIGW,
            totalNATGateways,
            totalVPCEndpoints,
            totalPeeringConnections,
            totalTransitGatewayAttachments
        };
    }

    /**
     * Récupère les régions actives
     */
    getActiveRegions() {
        const regions = [...new Set(this.vpcs.map(vpc => vpc.region))];
        return regions.filter(r => r).sort();
    }

    /**
     * Filtre les VPCs par région
     */
    filterByRegion(region) {
        if (!region || region === 'all') {
            return this.vpcs;
        }
        return this.vpcs.filter(vpc => vpc.region === region);
    }

    /**
     * Filtre les VPCs par état
     */
    filterByState(state) {
        if (!state || state === 'all') {
            return this.vpcs;
        }
        return this.vpcs.filter(vpc => vpc.state === state);
    }
}

