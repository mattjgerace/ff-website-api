import time
from django.db import OperationalError, connections

def wait_for_db(max_attempts=10, delay=1):
    for _ in range(max_attempts):
        try:
            connections['default'].cursor()
            return True
        except OperationalError:
            time.sleep(delay)
    return False

def wait_for_mongo(db, max_attempts=10, delay=1):
    for _ in range(max_attempts):
        try:
            db.command("ping")
            return True
        except Exception as e:
            time.sleep(delay)
    return False
