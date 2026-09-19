with open(".github/workflows/daily_injection.yml", "r") as f:
    c = f.read()
c = c.replace("pytest tests/ -v --tb=short -x -m critical --junitxml=pytest-results.xml", "python -m pytest tests/ -v --tb=short -x -m critical || (echo 'PYTEST FAILED, DUMPING LOGS:' && cat pytest-results.xml && exit 1)")
with open(".github/workflows/daily_injection.yml", "w") as f:
    f.write(c)
