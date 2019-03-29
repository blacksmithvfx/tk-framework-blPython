import pytest
from pytest import raises, fixture

import sys, os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../../')
sg_core_path = r'C:\Users\Blacksmith\AppData\Roaming\Shotgun\blacksmith\p300c125.basic.desktop\cfg\install\core\python'
sys.path.append('S:\pipeline\shotgun\python-api')
sys.path.append(sg_core_path)

import tank, sgtk
import shotgun_api3
import blPython.shotgun

PROJECT_ID = 314
ENGINES = {'tk-shell', 'tk-desktop', 'tk-nuke'}

@pytest.fixture()
def sg():
    os.environ['BL_DEVMODE'] = 'True'
    # Setup SG session
    sg = shotgun_api3.Shotgun("https://blacksmith.shotgunstudio.com",
                              login="Blacksmith",
                              password="Bl@cksmith01")

    yield sg

@pytest.fixture()
def engine():
    os.environ['BL_DEVMODE'] = 'True'
    import sgtk
    # Start up a Toolkit Manager
    mgr = sgtk.bootstrap.ToolkitManager()
    mgr.base_configuration = r"sgtk:descriptor:dev?path=S:\pipeline\blk_sg_config\shotgun-config\master"
    e = mgr.bootstrap_engine("tk-shell", entity={"type": "Project", "id": PROJECT_ID})
    import sgtk

    # self.tk = self.e.sgtk
    # self.project = sg.find('Project', [['id', 'is', 300]])
    yield e

class TestShotgunEnv(object):
    #def __init__(self):

    def test_sg(self, engine, sg):
        blPython.shotgun.env.Env.sg = sg
        blPython.shotgun.env.Env.context = engine.context

        blPython.shotgun.env.Env.get_user_env
        env = blPython.shotgun.get_env('tk-desktop', engine.context)
        print env
        #assert isinstance(self.sg, tank.api.Tank)



