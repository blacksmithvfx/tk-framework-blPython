from unittest import TestCase
from blPython.scripts.tools import sg_packager

class TestZip_branch(TestCase):

    VALID_PATHS = [
        r'S:\pipeline\blk_sg_config\shotgun-config\users\pm\shotgun-config']
    INVALID_PATHS = [r'C:\\Users\\Blacksmith\\Documents\\git_repos\\shotgun-config\\release\\episodic',
                     r'C:\\Users\\Blacksmith\\Documents\\git_repos\\shotgun-config\\release\\episodic\\descriptor-episodic-v1.1.7.0.1.1']

    def test_zip_sg_config_valid_paths(self):
        for path in self.VALID_PATHS:
            result = sg_packager.zip_branch(path)
            print result
            if not result:
                self.fail()

    def test_zip_sg_config_invalid_paths(self):
        for path in self.INVALID_PATHS:
            self.assertRaises(ValueError, sg_packager.zip_branch, path)


