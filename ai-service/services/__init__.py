# This file makes 'services' a Python package
import logging
import importlib
import importlib.util

def import_service(module_name):
    try:
        return importlib.import_module(f".{module_name}", package=__name__)
    except ImportError as e:
        logging.error(f"Failed to import {module_name}: {e}. This may be due to a missing or incorrect service module.")
        raise
    except ModuleNotFoundError as e:
        logging.error(f"Module {module_name} not found: {e}. Please ensure the module is installed and available.")
        raise

try:
    service1 = import_service("service1")
    service2 = import_service("service2")
except (ImportError, ModuleNotFoundError) as e:
    logging.critical(f"Critical import error: {e}. Aborting process.")
    exit(1)