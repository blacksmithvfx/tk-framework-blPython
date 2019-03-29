"""
Necessary Documentation of the code

Blacksmith VFX Global Variables

A handy collection of values that might be used across many modules and methods.

Author: Patrick Macdonald
Template Author: Patrick Macdonald
"""
import os
import json

# r'C:\Users\Blacksmith\Documents\GitHub\pipeline\Python\shotgun\shotgun_config.json'
#SHOTGUN_CONFIG_PATH = os.path.join()

# with open(SHOTGUN_CONFIG_PATH) as f:
#     config = json.load(f)

config = {
  "SHOTGUN_SITE": "https://blacksmith.shotgunstudio.com",
  "TOOL_CONFIGURATION_ENTITY_NAME": "CustomEntity01"
}

# Current SG Core location. Add this to sys.path to be able to import sgtk when outside normal SG ecosystem.
SG_CORE_VERSION = '0.18.158'
# SG_CORE_MODULES = r'S:\pipeline\shotgun\core\current\install\app_store\tk-core\v%s\python' % SG_CORE_VERSION
SG_CORE_MODULES = r'\\blacksmith01\blacksmithSS\pipeline\shotgun\core\current\install\app_store\tk-core\v0.18.153\python' #r'\\blacksmith01\blacksmithSS\pipeline\shotgun\core\current\install\app_store\tk-core\v%s\python' % SG_CORE_VERSION


# Path to the SG Python API repo. Add this to sys.path to be able to import shotgun_api3
#SG_API_PATH = r'S:\pipeline\shotgun\python-api'
SG_API_PATH = r'\\blacksmith01\blacksmithSS\pipeline\shotgun\python-api'


# Path to 3rd party packages installed on shared Python27 Install
BLACKSMITH_SITE_PACKAGES = r'S:\pipeline\Python\Python27\Lib\site-packages'

# Blacksmith SG website URLE
SHOTGUN_SITE = config['SHOTGUN_SITE']

# Entity_dict
CUSTOM_ENTITIES = {
  'Environment' : 'CustomNonProjectEntity02',
}

GLOBAL_ENVIRONMENT_ID = 3
