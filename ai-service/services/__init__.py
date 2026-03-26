# This file makes 'services' a Python package
try:
    from . import service1, service2
except Exception as e:
    print(f"Error importing services: {str(e)}")