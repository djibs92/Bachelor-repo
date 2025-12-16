#Pipeline CI/CD  Clouddiagnoze avec Dagger 
import dagger 
from dagger import dag, function, object_type 


@object_type
class Clouddiagnoze:
    "The Pipeline for Clouddiagnoze"
    @function
    def test(self,source: dagger.Directory)->  dagger.Container:
        """Lance les tests pytest du backend"""
        return (
            dag.container()
            .from_("python:3.11-slim")
            #Installer les dépendances système
            .with_exec(["apt-get","update"])
            .with_exec(["apt-get","install","-y","gcc","libmariadb-dev","pkg-config"])
            .with_directory("/app",source)
            .with_workdir("/app")
            #Installer les dépendances Python
            .with_exec(["pip","install","--no-cache-dir","-r","requirements.txt"])
            #Lancer les tests
            .with_exec(["pytest","-v","--tb=short"])
        ) 
    @function
    async def test_and_report(self, source: dagger.Directory) -> str:
        """Lancer les tests et retourne le resultat"""
        return await self.test(source).stdout()



    @function
    def build_backend(self, source: dagger.Directory) -> dagger.Container:
        """Build l'image Docker du backend"""
        return dag.container().build(source, dockerfile="Dockerfile.backend")

    @function
    def build_frontend(self, source: dagger.Directory) -> dagger.Container:
        """Build l'image du frontend"""
        return dag.container().build(source, dockerfile="Dockerfile.frontend")
    
    @function 
    async def ci(self,source: dagger.Directory) -> str:
        """Pipeline CI complet : test + build"""
        #1. Lancer les tests 
        test_output = await self.test(source).stdout()

        await self.build_backend(source).sync()

        await self.build_frontend(source).sync()

        return f"CI Passed\n\n{test_output}"

 
