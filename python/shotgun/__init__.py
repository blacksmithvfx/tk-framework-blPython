import sgtk
import env
logger = sgtk.LogManager.get_logger(__name__)

def get_env(engine_name, context): #(engine_name=sgtk.platform.current_engine().name, context=sgtk.platform.current_engine().context):
    logger.debug(". get_env()")
    reload(env)
    return env.Env(engine_name, context)
