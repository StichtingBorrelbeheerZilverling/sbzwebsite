from settings.default import *

# Try to import local settings, fallback to config via environment variables if that fails
try:
	from settings.local import *
except ImportError:
	from settings.environ import *
