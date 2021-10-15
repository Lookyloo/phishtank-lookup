env_global_name: str = 'PHISHTANK_HOME'

from .exceptions import PhishtankException  # noqa

# NOTE: the imports below are there to avoid too long paths whe importing the
# classes/methods in the rest of the project while keeping all tha tin a subdirectory
# and allow to update them easily.
# You should not have to change anything in this directory besides the variable above.

from .abstractmanager import AbstractManager  # noqa

from .exceptions import MissingEnv, CreateDirectoryException, ConfigError  # noqa

from .helpers import get_homedir, load_configs, get_config, safe_create_dir, get_socket_path, try_make_file  # noqa