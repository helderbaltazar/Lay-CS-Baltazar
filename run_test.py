from tests.unit.test_scanner import test_rank_by_target

print("Starting test")
try:
    test_rank_by_target()
    print("Done")
except Exception as e:
    print(f"Error: {e}")
