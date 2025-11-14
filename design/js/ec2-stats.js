/**
 * Calculs des statistiques EC2 pour le dashboard
 */

class EC2Stats {
    constructor() {
        this.instances = [];
    }

    /**
     * Charge les instances EC2 depuis l'API
     */
    async loadInstances() {
        try {
            const data = await api.getEC2Instances({ limit: 100 });
            this.instances = data.instances || [];
            console.log(`✅ ${this.instances.length} instances EC2 chargées`);
            return this.instances;
        } catch (error) {
            console.error('❌ Erreur chargement instances EC2:', error);
            throw error;
        }
    }

    /**
     * Calcule le total d'instances et la répartition par état
     */
    getTotalInstancesStats() {
        const total = this.instances.length;
        const byState = {};

        this.instances.forEach(instance => {
            const state = instance.state || 'unknown';
            byState[state] = (byState[state] || 0) + 1;
        });

        return {
            total,
            running: byState.running || 0,
            stopped: byState.stopped || 0,
            terminated: byState.terminated || 0,
            other: total - (byState.running || 0) - (byState.stopped || 0) - (byState.terminated || 0),
            byState
        };
    }

    /**
     * Calcule les régions actives
     */
    getRegionsStats() {
        const regionCounts = {};

        this.instances.forEach(instance => {
            const region = instance.region || 'unknown';
            regionCounts[region] = (regionCounts[region] || 0) + 1;
        });

        // Trouver la région la plus utilisée
        let topRegion = null;
        let maxCount = 0;
        Object.entries(regionCounts).forEach(([region, count]) => {
            if (count > maxCount) {
                maxCount = count;
                topRegion = region;
            }
        });

        return {
            totalRegions: Object.keys(regionCounts).length,
            topRegion,
            topRegionCount: maxCount,
            byRegion: regionCounts
        };
    }

    /**
     * Calcule le CPU moyen global (uniquement instances running)
     */
    getAverageCPU() {
        const runningInstances = this.instances.filter(i => i.state === 'running');
        
        if (runningInstances.length === 0) {
            return { average: 0, count: 0 };
        }

        const cpuValues = runningInstances
            .filter(i => i.performance && i.performance.cpu_utilization_avg !== null)
            .map(i => i.performance.cpu_utilization_avg);

        if (cpuValues.length === 0) {
            return { average: 0, count: 0 };
        }

        const sum = cpuValues.reduce((acc, val) => acc + val, 0);
        const average = sum / cpuValues.length;

        return {
            average: average.toFixed(2),
            count: cpuValues.length,
            min: Math.min(...cpuValues).toFixed(2),
            max: Math.max(...cpuValues).toFixed(2)
        };
    }

    /**
     * Calcule le trafic réseau total
     */
    getNetworkTrafficStats() {
        let totalIn = 0;
        let totalOut = 0;

        this.instances.forEach(instance => {
            if (instance.performance) {
                totalIn += instance.performance.network_in_bytes || 0;
                totalOut += instance.performance.network_out_bytes || 0;
            }
        });

        const total = totalIn + totalOut;

        return {
            total,
            totalIn,
            totalOut,
            totalFormatted: this.formatBytes(total),
            inFormatted: this.formatBytes(totalIn),
            outFormatted: this.formatBytes(totalOut)
        };
    }

    /**
     * Répartition par type d'instance
     */
    getInstanceTypeDistribution() {
        const typeCounts = {};

        this.instances.forEach(instance => {
            const type = instance.instance_type || 'unknown';
            typeCounts[type] = (typeCounts[type] || 0) + 1;
        });

        // Convertir en tableau pour Chart.js
        const labels = Object.keys(typeCounts);
        const data = Object.values(typeCounts);

        return {
            labels,
            data,
            byType: typeCounts
        };
    }

    /**
     * Répartition par état avec détails par région
     */
    getStateDistribution() {
        const stateCounts = {};
        const stateByRegion = {};

        this.instances.forEach(instance => {
            const state = instance.state || 'unknown';
            const region = instance.region || 'unknown';

            // Compter par état
            stateCounts[state] = (stateCounts[state] || 0) + 1;

            // Compter par état et région
            if (!stateByRegion[state]) {
                stateByRegion[state] = {};
            }
            stateByRegion[state][region] = (stateByRegion[state][region] || 0) + 1;
        });

        const labels = Object.keys(stateCounts);
        const data = Object.values(stateCounts);

        return {
            labels,
            data,
            byState: stateCounts,
            byStateAndRegion: stateByRegion
        };
    }

    /**
     * CPU par instance (top 10)
     */
    getCPUByInstance() {
        const instancesWithCPU = this.instances
            .filter(i => i.performance && i.performance.cpu_utilization_avg !== null)
            .map(i => ({
                name: i.tags?.Name || i.instance_id,
                instanceId: i.instance_id,
                cpu: i.performance.cpu_utilization_avg
            }))
            .sort((a, b) => b.cpu - a.cpu)
            .slice(0, 10); // Top 10

        const labels = instancesWithCPU.map(i => i.name);
        const data = instancesWithCPU.map(i => i.cpu);

        return {
            labels,
            data,
            instances: instancesWithCPU
        };
    }

    /**
     * Trafic réseau par instance (top 10)
     */
    getNetworkByInstance() {
        const instancesWithNetwork = this.instances
            .filter(i => i.performance && (i.performance.network_in_bytes || i.performance.network_out_bytes))
            .map(i => ({
                name: i.tags?.Name || i.instance_id,
                instanceId: i.instance_id,
                networkIn: i.performance.network_in_bytes || 0,
                networkOut: i.performance.network_out_bytes || 0,
                total: (i.performance.network_in_bytes || 0) + (i.performance.network_out_bytes || 0)
            }))
            .sort((a, b) => b.total - a.total)
            .slice(0, 10); // Top 10

        const labels = instancesWithNetwork.map(i => i.name);
        const dataIn = instancesWithNetwork.map(i => i.networkIn);
        const dataOut = instancesWithNetwork.map(i => i.networkOut);

        return {
            labels,
            dataIn,
            dataOut,
            instances: instancesWithNetwork
        };
    }

    /**
     * Détecte les alertes/insights
     */
    getAlerts() {
        const alerts = [];

        // Instances sans IP publique
        const noPublicIP = this.instances.filter(i => !i.public_ip && i.state === 'running');
        if (noPublicIP.length > 0) {
            alerts.push({
                type: 'warning',
                message: `${noPublicIP.length} instance(s) running sans IP publique`,
                count: noPublicIP.length,
                instances: noPublicIP.map(i => i.instance_id)
            });
        }

        // CPU élevé (> 80%)
        const highCPU = this.instances.filter(i => 
            i.state === 'running' && 
            i.performance && 
            i.performance.cpu_utilization_avg > 80
        );
        if (highCPU.length > 0) {
            alerts.push({
                type: 'critical',
                message: `${highCPU.length} instance(s) avec CPU > 80%`,
                count: highCPU.length,
                instances: highCPU.map(i => `${i.instance_id} (${i.performance.cpu_utilization_avg}%)`)
            });
        }

        // Instances sans tag "Name"
        const noNameTag = this.instances.filter(i => !i.tags || !i.tags.Name);
        if (noNameTag.length > 0) {
            alerts.push({
                type: 'info',
                message: `${noNameTag.length} instance(s) sans tag "Name"`,
                count: noNameTag.length,
                instances: noNameTag.map(i => i.instance_id)
            });
        }

        // Instances stopped (coût inutile)
        const stopped = this.instances.filter(i => i.state === 'stopped');
        if (stopped.length > 0) {
            alerts.push({
                type: 'warning',
                message: `${stopped.length} instance(s) stopped (coût EBS)`,
                count: stopped.length,
                instances: stopped.map(i => i.instance_id)
            });
        }

        return alerts;
    }

    /**
     * Formate les bytes en unité lisible
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Formate un nombre avec séparateurs
     */
    formatNumber(num) {
        return new Intl.NumberFormat('fr-FR').format(num);
    }
}

// Instance globale
const ec2Stats = new EC2Stats();

