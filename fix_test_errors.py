import re

# 1. Fix target_probabilities
with open('tests/unit/test_scanner.py', 'r') as f:
    content = f.read()
content = content.replace("'target_probabilities'", "'probabilities'")
with open('tests/unit/test_scanner.py', 'w') as f:
    f.write(content)

# 2. Fix test_full_pipeline.py to use in-memory DB
with open('tests/integration/test_full_pipeline.py', 'r') as f:
    content = f.read()

old_fixture = """@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
"""

new_fixture = """@pytest.fixture(autouse=True)
def setup_db():
    from sqlalchemy import create_engine
    import database.db
    test_engine = create_engine("sqlite:///:memory:")
    database.db.engine = test_engine
    database.db.SessionLocal.configure(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
"""
if old_fixture in content:
    content = content.replace(old_fixture, new_fixture)
    with open('tests/integration/test_full_pipeline.py', 'w') as f:
        f.write(content)
