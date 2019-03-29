import os
import sys
import ast
import pprint

import shotgun_api3
import sgtk
import tank
import blPython
import blPython.core._sys
reload(blPython.core._sys)

logger = sgtk.LogManager.get_logger(__name__)

class Env:
    def __init__(self, engine_name, context):
        """

        :param engine: The engine-name
        :param context:  The SG context entity
        """
        logger.debug("Initialising SG Environment")

        self.env = {}
        self.engine_name = engine_name
        self.context = context

        if not isinstance(context, tank.context.Context):
            raise ValueError("Supplied context is not a valid SG context : %s" % context)

        self.sg = self.get_sg()
        self.project = self.get_project(context.project)

        # Get Studio env
        studio_env_id = 3
        logger.debug(". Getting Studio env...")
        self.env.update( self.parse_env( [ {'type':blPython.custom_entities['Environment'], 'id': studio_env_id} ] ) )
        #logger.debug("\nenv : {}".format(self.env))

        # Get Engine Env
        logger.debug(". Getting Engine env...{}".format(self.engine_name))
        engine_env = self.get_engine_env()
        self.env.update( engine_env  )
        #logger.debug("\nenv : {}".format(self.env))

        # Get Project Env
        logger.debug(". Getting Project env...")
        project_env = self.get_project_env()
        #logger.debug("# project_env : {}".format(project_env))
        self.env.update( project_env )
        # logger.debug("\nenv : {}".format(self.env))

        # Get User Env
        logger.debug(". Getting User env...")

        user_env = self.get_user_env()
        # logger.debug("# user_env : {}".format(user_env))
        self.env.update( user_env )

        logger.debug("\n. Final env : {}".format(pprint.pformat(self.env)))

        # self.env.update(ast.literal_eval())

    def get_user_env(self):
        user = self.sg.find_one('HumanUser', [['id', 'is', self.context.user['id']]], ['sg_env'])

        user_env_entities = self.sg.find(blPython.custom_entities['Environment'],[['human_user_sg_env_human_users','in',user]],['sg_json','sg_parent','code'])
        if user_env_entities:
            return self.parse_env(user_env_entities)
        else:
            return {}

    def get_project_env(self):
        if self.project['sg_env']:
            return self.parse_env( [ self.project['sg_env'] ] )
        else:
            return {}

    def get_engine_env(self):
        engine_software = self.sg.find_one("Software", [['project_sg_software_projects', 'in', self.context.project], ['engine','is',self.engine_name]], ['code', 'sg_env'])

        print("engine_software : {}".format(engine_software))
        if engine_software:
            if engine_software.get('sg_env'):
                return self.parse_env( [ engine_software.get('sg_env') ])

        return {}

    def get_environment_recursive(self, id):
        envs = []

        result = self.sg.find_one(blPython.custom_entities['Environment'],[['id','is',id]],['sg_json','sg_parent','code'])
        if result:
            if result['sg_json']:
                envs.append(result)

            if result['sg_parent']:
                parent = self.get_environment_recursive(result['sg_parent']['id'])
                envs += parent

        return envs

    def parse_env(self, env_entities):
        env = {}
        # logger.debug(env_entities)
        for env_entity in env_entities:
            envs = self.get_environment_recursive(env_entity['id'])
            envs.reverse()

            for i in envs:
                env_data = ast.literal_eval(i['sg_json'])
                env.update(env_data)

        return env

    def set_env(self):
        logger.debug("Updating environment...")
        for key in self.env.keys():

            item = self.env[key]
            logger.debug(". {} : {} : {}".format(key, item['action'], item['value']))

            if item['action'] == 'set':
                os.environ[key] = item['value']

            elif item['action'] == 'append':
                if key == 'PYTHONPATH':
                    logger.debug(". . Adding {} to sys.path".format(item['value']))
                    blPython.core._sys.AddSysPath(item['value'])
                else:
                    blPython.core._sys.append_to_environment_variable(key, item['value'])

                # os.environ[key] = os.environ[key] + os.pathsep + item['value']

        logger.debug("\nUpdated environment : ")

        logger.debug(". Environment : ")

        for key in self.env.keys():
            logger.debug(". . {} : {}".format(key, os.environ.get(key, 'NOTFOUND')))

        logger.debug("\n. sys.path : ")
        for path in sys.path:
            logger.debug(". . {}".format(path))

    def get_studio_env(self):
        env_global = self.sg.find_one(blPython.custom_entities['Environment'],[['code','is','Global']],['sg_json', 'sg_parent'])

    def get_project(self, project):
        # logger.debug("get_project({})".format(project['id']))
        result = self.sg.find_one('Project',[['id','is',project['id']]],['sg_env', 'sg_software'])
        # logger.debug("result : {}".format(result))
        return result

    def get_sg(self):
        return get_sg()

    def get_engine(self):
        return get_engine()

    def get_sequence_env(self):
        pass

    def get_shot_env(self):
        pass

    def get_task_env(self):
        pass



def get_engine():
    sgtk.platform.current_engine()

def get_sg():
    sg = shotgun_api3.Shotgun("https://blacksmith.shotgunstudio.com",
                          script_name="blPython",
                          api_key="p7s&cwqohkxaNiwujgeombrsx")
    if not sg:
        raise RuntimeError("Unable to authenticate Script User for blPython")
    else:
        return sg