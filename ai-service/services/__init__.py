# This file makes 'services' a Python package
import logging
import importlib
import importlib.util
import sys

def import_service(module_name):
    try:
        return importlib.import_module(f".{module_name}", package=__name__)
    except ImportError as e:
        logging.error(f"Failed to import {module_name}: {e}. This may be due to a missing or incorrect service module. Module name: {module_name}, Error type: {type(e).__name__}, Error message: {str(e)}")
        raise
    except ModuleNotFoundError as e:
        logging.error(f"Module {module_name} not found: {e}. Please ensure the module is installed and available. Module name: {module_name}, Error type: {type(e).__name__}, Error message: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred while importing {module_name}: {e}. Module name: {module_name}, Error type: {type(e).__name__}, Error message: {str(e)}")
        raise

try:
    service1 = import_service("service1")
    service2 = import_service("service2")
except ImportError as e:
    logging.critical(f"Critical import error: {e}. Aborting process. Error type: {type(e).__name__}, Error message: {str(e)}")
    exit(1)
except ModuleNotFoundError as e:
    logging.critical(f"Critical module not found error: {e}. Aborting process. Error type: {type(e).__name__}, Error message: {str(e)}")
    exit(1)
except Exception as e:
    logging.critical(f"An unexpected critical error occurred: {e}. Aborting process. Error type: {type(e).__name__}, Error message: {str(e)}")
    exit(1)