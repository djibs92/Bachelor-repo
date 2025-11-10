/**
 * Script de débogage pour tester les appels API
 */

async function debugAPI() {
    console.log('=== DEBUG API ===');
    
    // 1. Vérifier le token
    const token = authManager.getToken();
    console.log('Token JWT:', token ? 'Présent ✅' : 'Absent ❌');
    
    // 2. Vérifier l'utilisateur
    const user = authManager.getUser();
    console.log('Utilisateur:', user);
    
    // 3. Tester l'endpoint EC2
    console.log('\n=== TEST EC2 INSTANCES ===');
    try {
        const ec2Response = await fetch('http://localhost:8000/api/v1/ec2/instances?latest_only=true&limit=5', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Status EC2:', ec2Response.status);
        const ec2Data = await ec2Response.json();
        console.log('Données EC2:', ec2Data);
    } catch (error) {
        console.error('Erreur EC2:', error);
    }
    
    // 4. Tester l'endpoint S3
    console.log('\n=== TEST S3 BUCKETS ===');
    try {
        const s3Response = await fetch('http://localhost:8000/api/v1/s3/buckets?latest_only=true&limit=5', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Status S3:', s3Response.status);
        const s3Data = await s3Response.json();
        console.log('Données S3:', s3Data);
    } catch (error) {
        console.error('Erreur S3:', error);
    }
    
    // 5. Tester via l'API wrapper
    console.log('\n=== TEST VIA API WRAPPER ===');
    try {
        const ec2Data = await api.getEC2Instances({ limit: 5 });
        console.log('EC2 via wrapper:', ec2Data);
    } catch (error) {
        console.error('Erreur wrapper EC2:', error);
    }
}

// Exécuter au chargement de la page
if (typeof window !== 'undefined') {
    window.debugAPI = debugAPI;
    console.log('💡 Tapez debugAPI() dans la console pour tester les appels API');
}

