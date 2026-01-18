import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--port",
        action="store",
        default='COM20',
        help="Port to run the discovery tool on"
    )

@pytest.fixture(scope='session')
def port(request):
    return request.config.getoption("--port")
