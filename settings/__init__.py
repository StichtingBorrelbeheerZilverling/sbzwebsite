# Load default settings
from .default import *

# Load local settings
try:
    from .local import *
except ImportError:
    pass
