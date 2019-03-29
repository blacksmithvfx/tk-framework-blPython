import sys, os

def AddSysPath(new_path):
    """ AddSysPath(new_path): adds a directory to Python's sys.path

    Does not add the directory if it does not exist or if it's already on
    sys.path. Returns 1 if OK, -1 if new_path does not exist, 0 if it was
    already on sys.path.
    """

    # Avoid adding nonexistent paths
    if not os.path.exists(new_path): return -1

    # Standardize the path. Windows is case-insensitive, so lowercase
    # for definiteness.
    new_path = os.path.abspath(new_path)
    if sys.platform == 'win32':
        new_path = new_path.lower(  )

    # Check against all currently available paths
    for x in sys.path:
        x = os.path.abspath(x)
        if sys.platform == 'win32':
            x = x.lower(  )
        if new_path in (x, x + os.sep):
            print(". Not adding path to sys.path: %s" % new_path)
            return 0

    #sys.path.append(new_path)
    sys.path.insert(0, new_path)
    print(". Adding path to sys.path: %s" % new_path)
    return 1

def append_to_environment_variable(key, path):
    """ append_to_environment_variable(path): adds a directory to an environment vcariable

    Does not add the directory if it does not exist or if it's already on
    sys.path. Returns 1 if OK, -1 if new_path does not exist, 0 if it was
    already on sys.path.
    """

    # Avoid adding nonexistent paths
    if not os.path.exists(path): return -1

    # Standardize the path. Windows is case-insensitive, so lowercase
    # for definiteness.
    path = os.path.abspath(path)
    if sys.platform == 'win32':
        path = path.lower(  )

    # Check against all currently available paths
    for x in os.environ[key].split(os.pathsep):
        x = os.path.abspath(x)
        if sys.platform == 'win32':
            x = x.lower(  )
        if path in (x, x + os.sep):
            self.log.debugprint(". Not adding path to environment variable: %s" % path)
            return 0

    #sys.path.append(new_path)
    sys.path.insert(0, path)
    os.environ[key] = os.environ[key] + os.pathsep + path
    print(". Added path to os.environ[{}]: {}".format(key, path))
    return 1