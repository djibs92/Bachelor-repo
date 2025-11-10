/**
 * Optimisation du chargement des pages pour des transitions fluides
 */

// Afficher le loader au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Masquer le loader après le chargement complet
    window.addEventListener('load', function() {
        const loader = document.getElementById('page-loader');
        if (loader) {
            setTimeout(() => {
                loader.classList.add('hidden');
                setTimeout(() => {
                    loader.style.display = 'none';
                }, 300);
            }, 200);
        }
    });

    // Optimiser les particules - réduire le nombre pour améliorer les performances
    const particles = document.querySelectorAll('.particle');
    if (particles.length > 5) {
        // Garder seulement 5 particules
        particles.forEach((particle, index) => {
            if (index >= 5) {
                particle.remove();
            }
        });
    }

    // Optimiser les mots-clés flottants - réduire les animations
    const keywords = document.querySelectorAll('.keyword, .floating-keyword');
    keywords.forEach(keyword => {
        // Réduire la durée d'animation pour plus de fluidité
        keyword.style.animationDuration = '6s';
    });
});

// Précharger les pages pour des transitions plus rapides
function preloadPage(url) {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = url;
    document.head.appendChild(link);
}

// Précharger les pages principales au chargement
window.addEventListener('load', function() {
    setTimeout(() => {
        preloadPage('dashbord.html');
        preloadPage('dashboard-ec2.html');
        preloadPage('dashboard-s3.html');
        preloadPage('config-scan-new.html');
        preloadPage('settings.html');
    }, 1000);
});

