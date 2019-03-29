"""
Utility methods for working with events.
"""
import os

def is_dev_script(script_path):
    '''
    If the plugin's parent folder is called 'dev' return True
    :param script_path:
    :return:
    '''
    path_parts = os.path.dirname(script_path).split('\\')
    script_mode = path_parts[-1]
    result = script_mode == 'dev'
    return result

def is_valid_event(plugin_path, event, sg, logger):
    '''
    To prevent running event plugins on live projects during development, we launch
    the event daemon in the foreground and set an env var, BLK_EVENTS_DEV to True.
    When set, events will only run if the event is coming from a project whose type is set to "Dev".

    If the env var is not set, then all valid events will be processed by the plugin.

    :param event:
    :return:
    '''

    IS_DEV_SCRIPT = is_dev_script(plugin_path)

    # Get the project entity and get it's sg_type field.
    if event['project']:
        project_entity = sg.find_one(event['project']['type'],
                                     filters=[['id', 'is', event['project']['id']]],
                                     fields=['sg_type'])

    else:
        project_entity = sg.find_one(event['meta']['entity_type'],
            filters=[['id','is',event['meta']['entity_id']]],
            fields=['sg_type'])

    if not project_entity:
        return False

    logger.info('event : %s' % event)
    logger.info('project : %s' % project_entity)

    is_dev_mode = os.environ.get('BLK_EVENTS_DEV', False) # This is set before launching the daemon to set up us as a dev environment
    is_dev_project = project_entity.get('sg_type') == 'Dev'

    # only run if in devmode and in a devproject
    # or if not in devmode run for all projects. (eg if run from the service.)
    event_is_valid = (is_dev_mode and is_dev_project and IS_DEV_SCRIPT) or (not is_dev_mode and not IS_DEV_SCRIPT)

    if event_is_valid:
        logger.info('This event is valid')
    else:
        logger.info('This event is invalid.\nThis is because :')
        logger.info('. BLK_EVENTS_DEV(%s) AND project type(%s) AND script type(%s) is not True' % (
            is_dev_mode, is_dev_project, IS_DEV_SCRIPT))
        logger.info(
            '. OR we are not in devmode(is_dev_mode:%s) AND this script is not in the live folder(IS_DEV_SCRIPT:%s).' % (
            is_dev_mode, IS_DEV_SCRIPT))

    return event_is_valid