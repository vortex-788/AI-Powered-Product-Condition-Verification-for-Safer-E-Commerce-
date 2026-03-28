# This file makes 'services' a Python package
import logging
try:
    from . import service1, service2
except (ImportError, ModuleNotFoundError) as e:
    logging.error(f"Failed to import services: {e}. This may be due to a missing or incorrect service module. Services attempted to import: service1, service2")