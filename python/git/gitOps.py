"""
Blacksmith VFX Git utilities
"""
import re, os, sys
import subprocess

def is_git_repository(path):
    """
    Returns true if a valid git repository is detected in the provided path.

    :param path: <string> path to check is a git repo.
    :return: True/False
    """
    try:
        git_status = subprocess.check_output(['git', '-C', path, 'status'])
        result = 'Not a git repository' not in git_status or 'fatal' not in git_status
        return result

    except subprocess.CalledProcessError as e:
        return False


def get_git_remote_url_from_path(path):
    """
    Gets the remote git URL from the provided path which must be a git repo checked out from a remote.

    :param path: Path to the local Git repo
    :return: String URL path to the remote repo
    """

    # get git output
    git_output = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'], cwd=path)

    # remove trailing newline
    git_output = git_output.replace('\n','')

    return git_output


def get_git_repo_name_from_path(path, sanitize=True):
    """
    Returns the git repo name from the git repo provided in the path argument.
    requirements : The git repo must be cloned from remote for this approach to work.

    :param path: Path to the local Git repo
    :param sanitize: default=True, sanitizes the git repo name if required.
    :return:
    """

    # get the git remote url
    git_output = get_git_remote_url_from_path(path)

    # get basename
    git_output = os.path.basename(git_output)

    # strip extension
    git_output = os.path.splitext(git_output)[0]

    if sanitize:
        # sanitise branchname
        git_output = re.sub('[^0-9a-zA-Z]+', '_', git_output)

    return git_output


def get_current_git_branch_from_path(path, strip_parent=True, sanitize=False):
    """
    Returns the branchname of the provided path.

    :param path: Path to the local Git repo
    :param strip_parent: If True, removes all parent paths from branhcname.
    :param sanitize: If True, replaces any non alpha-numeric characters with an underscore.

    :return: <string> git branchname of the provided path
    """

    # get git output
    git_output = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=path)

    # remove trailing newline
    git_output = git_output.replace('\n','')

    if strip_parent:
        # Removes everything before the last '/' so we're just left with the short branchname
        git_output = git_output.split('/')[-1]

    if sanitize:
        # sanitise branchname
        git_output = re.sub('[^0-9a-zA-Z]+', '_', git_output)

    return git_output

def get_current_commit_hash_from_path(path, short=True):
    """
    Gets the current commit hash of the repo specified in path.
    By default the short-form hash is returned. To get the full hash set the 'short' argument to False

    :param path: Path to the local Git repo
    :param short: Toggle to choose between short and long form commit hash.
    :return: string : The commit hash
    """
    # build git query
    args = ['git', 'rev-parse', '--verify', 'HEAD']

    if short:
        args.append('--short')

    # get git output
    git_output = subprocess.check_output(args, cwd=path)

    # remove trailing newline
    git_output = git_output.replace('\n','')

    return git_output


def get_current_commit_comment_from_path(path):
    """
    Gets the current comment of the current commit for the repo found at the provided path.
    If no comment is defined, then the commit hash(shortform) will be returned.
    :param path: Path to the local Git repo
    :return: String : The commit message
    """
    # build git query
    #args = ['git', 'log', '--format=%B', '-n', 'l', 'HEAD']
    args = ['git', 'show', '-s', '--format=%B']

    # get git output
    git_output = subprocess.check_output(args, cwd=path)

    # remove trailing newline
    git_output = git_output.replace('\n','')

    return git_output


def get_current_tags_from_path(path):
    """
    Gets the tags associated with the current commit from the repo located in path.

    :param path: Path to the local Git repo
    :return: List of tag strings
    """
    # build git query
    args = ['git', 'tag', '-l', '--points-at', 'HEAD']

    # get git output
    git_output = subprocess.check_output(args, cwd=path)

    # extract paths from result. Each tag will be seperated by a newline
    tags = [i for i in git_output.split('\n') if i != '']

    return tags

def repo_has_uncommitted_changes(path):
    """
    Checks if the local checkout has any uncommitted changes and returns True if any are found.

    :param path: Path to the local Git repo
    :return: List of tag strings
    """
    # build git query
    args = ['git', 'diff-index', '--quiet', 'HEAD']

    # get git output
    try:
        git_output = subprocess.check_output(args, cwd=path)
        return False
    except:
        return True

    return tags

def get_current_tag_messages_from_path(path):
    """
    Gets the messages of any tags found on the current commit.

    :param path: Path to the local Git repo
    :return: A single string with all tag messages concatenated.
    """
    tags = get_current_tags_from_path(path)

    tag_messages = ''
    for tag in tags:

        # build git query
        args = ['git', 'tag', '-l', '--format=\'%(contents)\'', tag]

        # get git output
        tag_message = subprocess.check_output(args, cwd=path).split('\'')[1]

        tag_messages += tag_message

    return tag_messages