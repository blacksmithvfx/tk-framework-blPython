"""
The repo_packager is a generalised version of the sg_packager. It creates a package report for the current
repo branch and zips the branch up in to a packge and saves it to the studio release path.

- The branch is also copied to a release folder.
- The packager prevents packaging of any branch not adhering to semantic versioning.
- It also prevents packaging of any branch not in the release/ branch.
- Uploading to SG is not currently implemented, but the basic logic has been carried over from the sg_packager.
- The packager will fail if it detects an existing release in the release path.

"""

import os, sys
import zipfile
import logging
import traceback
import argparse
import pprint
import json
import getpass
import datetime
import re
import shutil
import errno

from collections import OrderedDict

# Add path to sys.path for Blacksmith python modules
# Temporary logic to find the current release path relative to this file
# This should be removed once the repos are split and a studio wide BLPYTHON env var is in place.
if not os.environ.get('BLPYTHON'):
    tools_dir = os.path.dirname(__file__)
    scripts_dir = os.path.dirname(tools_dir)
    blPython_dir = os.path.dirname(scripts_dir)
    blPythonPackage_dir = os.path.dirname(blPython_dir)
    BL_PYTHON_PATH = blPythonPackage_dir #r'C:\Users\Blacksmith\Documents\GitHub\pipeline\Python'
else:
    BL_PYTHON_PATH = os.environ.get('BLPYTHON')

sys.path.append(BL_PYTHON_PATH)

# Get Blacksmith modules.
from blPython.core import config
from blPython.git import gitOps

# Add path to SG API (for shotgun_api3 and sgtk imports)
sys.path.append(config.SG_API_PATH)

# Get SG API
import shotgun_api3

# Global Variables
STUDIO_RELEASE_PATH = r'S:\pipeline\_release'
TESTING = True
DEBUG_MODE = False # Sets the logger to DEBUG if enabled.

# Setup logging
logger = logging.getLogger('zip_sg_config')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
if DEBUG_MODE:
    ch.setLevel(logging.DEBUG)
else:
    ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

def get_args():
    """
    Get the arguments and return them
    :return: parsed argument object
    """
    examples = """Examples: TODO"""

    parser = argparse.ArgumentParser(
        description='Create a zip archive of a Git repo and upload it to a SG File Entity. This tool will also upload any git metadata related to the \'metadata\' field of the SG \'attachment\' entity.',
        epilog=examples,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True)

    # TODO : Add argument to toggle uploading to SG
    # parser.add_argument('-i', '--pc_id', action="store", type=int, required=True, help='The pipeline configuration ID to upload the pc zip package to.')
    parser.add_argument('-p', '--path', action="store", required=False, type=str, help='The path of the pipeline configuration to zip and upload. If this argument is not specified, the current working directory will be used instead.')
    parser.add_argument('-u', '--upload', action="store", required=False, type=bool, default=False, help='Set this to True to upload the package to SG.')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()


def zipdir(path, ziph, ignore_dirs=['.git','.idea']):
    """
    Zips the contents of 'path' into zipfile ziph ignoring folders specified in 'ignore_dirs'
    :param path: Path to the local Git repo
    :param ziph:
    :param ignore_dirs: By default this method ignores git and pycharm folders.
    :return:
    """

    # Verify path is a directory
    if not os.path.isdir(path):
        raise ValueError('Path is not a valid directory.')

    # get the length of the path. This is used later to ensure the zipfile contents exclude the parent path
    length = len(path)

    for root, dirs, files in os.walk(path):
        folder = root[length:]  # path without "parent"

        # Exclude the .git and .idea folders from the zipfile
        for dir_to_ignore in ignore_dirs:
            if dir_to_ignore in dirs:
                dirs.remove(dir_to_ignore)

        # Add the files and remove the parent path
        for file in files:
            ziph.write(os.path.join(root, file), os.path.join(folder, file))


def create_git_release_report(path, report_type='json'):
    """
    Creates a report of type txt or json containing various useful data.

    :param path: Path to the git repo
    :param report_type: Valid values are 'json' or 'txt'
    :return: This function returns a dict containing:
        'data': A json encoded representation of the report,
        'report_path': The path to the report file
    """

    if report_type not in ['json', 'txt']:
        raise ValueError('Unrecognised report_type specified. Valid options are : \'json\' or \'txt\'')

    report_dict = OrderedDict()

    if gitOps.is_git_repository(path):

        # get the git remote url
        report_dict['repo_url'] = gitOps.get_git_remote_url_from_path(path)

        # get the git repo name
        report_dict['repo_name'] = gitOps.get_git_repo_name_from_path(path, sanitize=False)
        logger.debug('. git_repo_name : %s' % report_dict['repo_name'])

        # get the branchname
        report_dict['branch'] = gitOps.get_current_git_branch_from_path(path, strip_parent=False)
        logger.debug('. Current branch : %s' % report_dict['branch'])

        # get the current user, time and date
        report_dict['released_by'] = getpass.getuser()
        now = datetime.datetime.now()
        report_dict['released_at'] = now.strftime("%H:%M")
        report_dict['released_on'] = now.strftime("%m.%d.%Y")

        # get latest commit hash
        report_dict['commit'] = gitOps.get_current_commit_hash_from_path(path, short=True)
        report_dict['commit_comment'] = (gitOps.get_current_commit_comment_from_path(path))

        # get tag from path
        report_dict['tags'] = gitOps.get_current_tags_from_path(path)
        report_dict['tag_comment'] = gitOps.get_current_tag_messages_from_path(path)

        # Create the report
        if report_type == 'txt':
            # Get the report path
            report_file_name = 'package_info.txt'
            report_file_path = os.path.join(path, report_file_name)

            # Add the report path to the report
            report_dict['report_file_path'] = report_file_path

            # Build the text report
            report_str_arr = []
            report_str_arr.append('Git release Package Report\n')
            report_str_arr.append('--------------------------\n')

            for i in report_dict.keys():
                report_str_arr.append('%s : %s\n' % (i, report_dict[i]))

            # Write the text report
            report_file = open(report_file_path, "w")
            report_file.writelines(report_str_arr)
            report_file.close()

        elif report_type == 'json':
            # Convert the data to json
            json_report = json.dumps(report_dict)

            # Get the report path
            report_file_name = 'package_info.json'
            report_file_path = os.path.join(path, report_file_name)

            # Add the report path to the report
            report_dict['report_file_path'] = report_file_path

            # Open new json file if not exist it will create
            fp = open(report_file_path, 'w')

            # write to json file
            fp.write(json_report)

            # close the connection
            fp.close()

        logger.debug('. Finished release report : %s' % pprint.pformat(dict(report_dict)))

        return {'data':report_dict, 'report_path': report_file_path}
    else:
        raise ValueError('Path does not point to a valid git repo : %s' % path)

def copy(src, dest):
    """
    Copy method that copies a source file our directory to the provided path.

    :param src:
    :param dest:
    :return:
    """
    try:
        # Check if the source is a file or directory and use the correct shutil method accordingly.
        if os.path.isdir(src):
            shutil.copytree(src, dest, ignore=shutil.ignore_patterns())
        else:
            shutil.copy(src, dest)

    except OSError as e:
        # If the error was caused because the source wasn't a directory
        logger.debug('. e.errno : %s' % e.errno)
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, dest)
        else:
            raise RuntimeError('Directory not copied. Error: %s' % e)

def release_branch(path):
    """
    Utility to zip up the currently checked out branch of a git repository at the provided path.
    By default, the .git and .idea folders are excluded from the archive.
    The archive will be saved to the parent folder of the provided path.
    The archive label will be the name of the currently checked out branch.
    On success, the zipfile path is returned.
    :param path: Path to the local Git repo
    :return: path to the created zipfile.
    """
    # Check if path is valid git repo
    logger.debug('. Checking path is valid git repo : %s' % path)

    if gitOps.is_git_repository(path):
        logger.debug('. git repo confirmed.')

        # get the branchname
        current_branch_name = gitOps.get_current_git_branch_from_path(path)
        logger.debug('. Current branch : %s' % current_branch_name)

        # get the git repo name
        git_repo_name = gitOps.get_git_repo_name_from_path(path, sanitize=True)
        logger.debug('. git_repo_name : %s' % git_repo_name)

        # create the zipfile filename
        zipfile_filename = '%s_%s.zip' % (git_repo_name, current_branch_name)

        # create the zipfile path
        # The package will be saved to a 'release' folder in the parent folder of the repo

        # define the root release folder for the current git repo
        repo_release_path = os.path.join(STUDIO_RELEASE_PATH, git_repo_name)

        # define the branch folder for this release, this has to be a semantic version under the release branch
        # This is where the actual release will live.
        branch_release_path = os.path.join(repo_release_path, current_branch_name)

        # define the path to the zip package folder
        zip_release_path = os.path.join(repo_release_path, '_packages')

        # define the full zip filepath.
        zipfile_path = os.path.abspath(os.path.join(zip_release_path, zipfile_filename))

        # Check if this branch has already been released to the release folder.
        # If it has, we stop the package creation and tell the user to create a new release branch.
        # Got to be tough to be kind here... we don't want anything in the release folder getting overwritten!

        if os.path.exists(zipfile_path) or os.path.exists(branch_release_path):
            raise RuntimeError('A release already exists for this branch. Please version up this release.')

        # Create the destination paths
        # if not os.path.exists(branch_release_path):
        #     os.makedirs(branch_release_path)

        if not os.path.exists(zip_release_path):
            os.makedirs(zip_release_path)

        # create the report to include in the zipfile
        report = create_git_release_report(path, report_type='json')

        # create the zipfile
        try:
            logger.debug('. Creating zipfile : %s' % zipfile_path)
            zipf = zipfile.ZipFile(zipfile_path, 'w', zipfile.ZIP_DEFLATED)
            zipdir(path, zipf)
            zipf.close()

        except RuntimeError:
            logger.error('. Zipfile creation failed!\n. %s' % traceback.print_exc())

        # Checkout out the branch in the release folder
        # Initial simple implementation is to simply copy our source path in to the destination folder
        # TODO Perhaps this should be updated with an actual git checkout method.
        logger.debug('. Path : %s' % path)

        # Get the files and folders to copy
        files = os.listdir(path)

        for file in files:

            # Get the source path
            source = os.path.join(path,file)

            # If the source is a directory, add the folder to the destination path
            if os.path.isdir(source):
                dest_dir = os.path.join(branch_release_path,os.path.basename(source))
            else:
                # Otherwise set the destination path to the root of the branch release path
                dest_dir = branch_release_path

            # Copy the item
            logger.debug('. Copying %s to %s' % (source,dest_dir))
            copy(source, dest_dir)

        logger.debug('. Finished releasing package to %s' % pprint.pformat(branch_release_path))
        return (zipfile_path, branch_release_path, report)

    else:
        raise ValueError('Path does not point to a valid git repository.')


def upload_package_to_sg(pipeline_configuration_archive, pipeline_configuration_id, report_data=None):

    # NOT IMPLEMENTED YET
    # TODO : Updat this package to work with generic repos.

    logger.info('. Uploading config to pipeline configuration %s' % pipeline_configuration_id)
    logger.info('. report_data %s' % report_data)

    SHOTGUN_CONFIG_PATH = os.path.join(os.environ.get('PIPELINE_ROOT'), 'Python/shotgun/shotgun_config.json')

    with open(SHOTGUN_CONFIG_PATH) as f:
        config = json.load(f)

    sg = shotgun_api3.Shotgun(
        config["SHOTGUN_SITE"],
        'upload_pipeline_config_archive',
        'qInx7cbtvdxrhufmu~ezzszlb'
    )

    # get pipeline configuration
    pipeline_config = sg.find_one('PipelineConfiguration', [['id','is',pipeline_configuration_id]])

    if pipeline_config:
        logger.info('. Pipeline configuration valid. Processing upload now...')

        # upload archive
        uploaded_file_id = sg.upload('PipelineConfiguration',
                  pipeline_configuration_id,
                  pipeline_configuration_archive,
                  field_name="uploaded_config",
                  display_name=os.path.basename(pipeline_configuration_archive))

        logger.info('. pipeline_configuration_version : %s' % uploaded_file_id)

        # update descriptor

        # form the descriptor string
        descriptor_str = 'sgtk:descriptor:shotgun?entity_type=PipelineConfiguration&id=%s&field=uploaded_config&version=%s' % (pipeline_configuration_id, uploaded_file_id)
        logger.info('. descriptor_str : %s' % descriptor_str)
        logger.info('. Updating descriptor field')

        # prepare the update data
        data = {'descriptor' : descriptor_str,}

        # udate the entity
        update_pc_descriptor = sg.update('PipelineConfiguration',
                  pipeline_configuration_id,
                  data)

        logger.info('. PipelineConfiguration descriptor updated : %s' % update_pc_descriptor)


        # Add report/metadata to uploaded file(the SG 'Attachment') and set type

        data={}
        data['sg_type'] = 'PipelineConfiguration'

        if report_data:

            # Add the report dict to the metadata field of the attachment
            data['metadata'] = str(report_data)
            data['description'] = str(report_data.get('commit_comment',''))
            # This section is commented out as to implement this would require checking if the tags
            # already exist on SG and if not, creating them.
            # It may also not be desirable to pollute the studios 'tags' database with git tags in any case.

            # if len(report_data['tags'])>0:
            #     data['tags'] = report_data['tags']

        # udate the entity
        update_file_metadata_result = sg.update('Attachment',
                  uploaded_file_id,
                  data)

        logger.info('. Uploaded file metadata updated : %s' % update_file_metadata_result)

    else:
        logger.error('. Pipeline configuration does not exist. Please ensure the pipeline configuration with id %s exists.' % pipeline_configuration_id)

def sg_package_type(path):
    """
    Utility method to determine what kind of shotgun package is located in path.
    :param path:
    :return:
    """

    if is_sg_package(path):
        files = os.listdir(path)
        if 'core' in files and 'env' in files and 'hooks' in files:
            return 'tk-config'
        elif 'engine.py' in files:
            return 'tk-engine'
        elif 'app.py' in files:
            return 'tk-app'
        elif 'framework.py' in files:
            return 'tk-framework'
    else:
        raise RuntimeError("The path provided does not point to a valid SG package.")

def is_valid_repo(path):
    """
    Utility method to

    - determine if the path provided points to a valid Git Repo.
    - TODO Check current checkout has any un-committed changes.
    - test
    :param path:
    :return:
    """

    files = os.listdir(path)

    # TODO Define validation login

    # get the branchname
    current_branch_name = gitOps.get_current_git_branch_from_path(path, strip_parent=False)
    logger.debug('. current_branch_name : %s' % current_branch_name)

    # validate branch name
    # it must be of the form release/v#.#.#-alpha.something+meta-data
    # This pattern was derived from one found here : https://gist.github.com/jhorsman/62eeea161a13b80e39f5249281e17c39
    # which itself was derived from here : https://github.com/npm/node-semver/issues/32

    pattern = re.compile('^(release)\/v([0-9]|[1-9][0-9]*)\.([0-9]|[1-9][0-9]*)\.([0-9]|[1-9][0-9]*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+)?$')
    if re.match(pattern, current_branch_name):
        logger.debug('. branchname %s passes semantic versioning validation.' % current_branch_name)
    else:
        raise RuntimeError("The branch %s checked out at %s, does not have a valid release branch name. Please ensure it follows semantic versioning standards." % (current_branch_name, project_file_path))

    if gitOps.repo_has_uncommitted_changes(path):
        raise RuntimeError("The branch %s checked out at %s, has uncommitted changes. Please commit and push before trying again." % (current_branch_name, project_file_path))

    return True

if __name__ == "__main__":
    args = get_args()

    # Temporarily set this argument until logic is defined in get_args()
    args.upload_to_sg = False

    logger.info('. Running "repo_packager.py"')
    logger.debug('. args : %s' % pprint.pformat(vars(args)))

    # Run the script
    # Get the project filepath from the supplied arguments.
    if not args.path:
        project_file_path = os.getcwd()
    else:
        project_file_path = os.path.abspath(args.path)

    # Validate the repo
    if not is_valid_repo(project_file_path):
        raise RuntimeError("The path, %s, failed validation." % project_file_path)

    # Create the config archive
    logger.info('. %s is a valid release branch. Initiating release...' % project_file_path)
    pipeline_configuration_archive, branch_release_path, report = release_branch(project_file_path)

    logger.info('. Release package :  %s' % pipeline_configuration_archive)
    logger.info('. Release report : %s' % pprint.pformat(dict(report['data'])))

    if pipeline_configuration_archive and args.upload_to_sg:
        logger.info('. Zipfile successfully created : %s' % pipeline_configuration_archive)

        upload_package_to_sg(pipeline_configuration_archive, args.pc_id, report_data = report['data'])

    logger.info('. Finished releasing branch to : %s' % branch_release_path)






