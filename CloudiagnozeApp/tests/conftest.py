"""
Fixtures pytest partagées pour tous les tests CloudDiagnoze
"""
import pytest
import os
from faker import Faker

# Configuration pytest-asyncio et import des fixtures
pytest_plugins = (
    'pytest_asyncio',
    'tests.aws_tests.fixtures_ec2',
    'tests.aws_tests.fixtures_s3',
    'tests.aws_tests.fixtures_vpc',
    'tests.aws_tests.fixtures_rds',
)


@pytest.fixture(scope="session")
def faker_instance():
    """Instance Faker pour générer des données réalistes"""
    return Faker()


@pytest.fixture(scope="function", autouse=True)
def mock_aws_credentials():
    """
    Mock des credentials AWS pour éviter les erreurs.
    Appliqué automatiquement à tous les tests.
    """
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'eu-west-3'
    
    yield
    
    # Cleanup après le test
    for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 
                'AWS_SECURITY_TOKEN', 'AWS_SESSION_TOKEN', 'AWS_DEFAULT_REGION']:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def client_id():
    """Client ID pour les tests"""
    return "TEST-CLIENT-001"


@pytest.fixture
def test_regions():
    """Régions AWS pour les tests"""
    return ['eu-west-3', 'us-east-1']


@pytest.fixture
def single_region():
    """Une seule région pour les tests simples"""
    return 'eu-west-3'


@pytest.fixture
def mock_db_session(mocker):
    """
    Mock de la session de base de données SQLAlchemy.
    Utilisé pour les tests qui nécessitent une DB sans vraie connexion.
    """
    mock_session = mocker.MagicMock()
    mock_session.add = mocker.MagicMock()
    mock_session.commit = mocker.MagicMock()
    mock_session.flush = mocker.MagicMock()
    mock_session.rollback = mocker.MagicMock()
    return mock_session

