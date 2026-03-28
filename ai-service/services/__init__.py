# This file makes 'services' a Python package
import logging
try:
    from . import service1, service2
except Exception as e:
    logging.error(f"Error importing services: {str(e)}")