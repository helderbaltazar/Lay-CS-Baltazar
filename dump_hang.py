import faulthandler
import signal
faulthandler.register(signal.SIGALRM)
import os

from tests.unit.test_scanner import test_rank_by_target

signal.alarm(2)

print("Running test...")
test_rank_by_target()
print("Done")
