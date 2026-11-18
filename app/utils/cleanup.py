import shutil
from pathlib import Path
from contextlib import contextmanager
@contextmanager
def temporary_workspace(base="/tmp"):
    p=Path(__import__('tempfile').mkdtemp(prefix="intelkit-", dir=base))
    try: yield p
    finally: shutil.rmtree(p, ignore_errors=True)
