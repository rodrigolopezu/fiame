"""Los tests usan una base de datos temporal, nunca la de desarrollo."""
import os
import tempfile

os.environ["FIAME_BD"] = f"sqlite:///{tempfile.mkdtemp()}/fiame-test.db"
