import os
import json
from utils.syslogger import SysLogger

# Logfile is /tmp/protodpp.log
logger = SysLogger().logger()

default_key = "MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIgACDIBBiMf4W+tukQcNKz5eObkMp3tNPFJRvBhE1sop3K0="
default_p256 = "30570201010420777fc55dc51e967c10ec051b91d860b5f1e6c934e48d5daffef98d032c64b170a00a06082a8648ce3d030107a124032200020c804188c7f85beb6e91070d2b3e5e39b90ca77b4d3c5251bc1844d6ca29dcad"
default_vendor_code = "DAWG"
default_channel = 1
default_channel_class = 81
default_mode = "dpp"
default_countdown = 30
# proxy settings are used when simulating the iphone mobile application (click on qrcode)
default_proxy_mso_portal = "https://mso-portal-api.micronets.in"
default_proxy_username = "grandma"
default_proxy_password = "grandma"
default_proxy_device_uid = "AgoNDQcDDgg"

folder = os.path.dirname(os.path.realpath('__file__'))
filename = os.path.join(folder, '../config/config.json')

class Config():

    def __init__(self):

        #self.config = {}
        self.load_config()
        logger.info("load_config:")
        #logger.info(self.dump())
        #self.set_defaults()
        #self.save_config()

    def config_default(self, key, default):

        if not self.get(key):
            self.set(key, default)

    def save_config(self):
        #with open(filename, 'w') as outfile:  
        #    json.dump(self.config, outfile, sort_keys=True, indent=4, separators=(',', ': '))
        self.dump(filename)

    def set_defaults(self):
        # config defaults
        self.config_default('mode', 'dpp')
        self.config_default('key', default_key)
        self.config_default('p256', default_p256)
        self.config_default('vendorCode', default_vendor_code)
        self.config_default('channel', default_channel)
        self.config_default('channelClass', default_channel_class)
        self.config_default('countdown', default_countdown)
        self.config_default('demo', True)
        self.config_default('splash_animation_seconds', 10)
        self.config_default('onboard_animation_seconds', 5)

        self.config_default(['dppProxy','msoPortalUrl'], default_proxy_mso_portal)
        self.config_default(['dppProxy','username'], default_proxy_username)
        self.config_default(['dppProxy','password'], default_proxy_password)
        self.config_default(['dppProxy','deviceModelUID'], default_proxy_device_uid)

    def load_config(self):
        try:
            with open(filename, 'r') as infile:  
                file_data = infile.read()
                self.config = json.loads(file_data)

                logger.info("config loaded OK: "+str(len(self.config))+ " keys")
                #logger.info("\n" + json.dumps(config))

        except (OSError, IOError, KeyError) as e: # FileNotFoundError does not exist on Python < 3.3
            pass

    def dump(self, file=None):
        if not file:
            return json.dumps(self.config,  sort_keys=True, indent=4, separators=(',', ': '))
        else:
            with open(file, 'w') as outfile:  
                json.dump(self.config, outfile, sort_keys=True, indent=4, separators=(',', ': '))

    def set(self, key, value, dictionary=None):

        if not dictionary:
            dictionary = self.config

        if isinstance(key, list):
            # array of keys
            k0 = key.pop(0)
            if not k0 in dictionary:
                # This is an insert
                if len(key) == 0:
                    # no more keys, insert value
                    dictionary[k0] = value
                else:
                    dictionary[k0] = {}
                    self.set(key, value, dictionary[k0])
            else:
                # This is an update
                x = dictionary[k0]
                if isinstance(x, dict):
                    self.set(key, value, x)
                else:
                    dictionary[k0] = value
        else:
            # single key, update or insert
            dictionary[key] = value

    def get(self, key, default=None, dictionary=None):

        if not dictionary:
            dictionary = self.config

        if isinstance(key, list):
            # array of keys
            k0 = key.pop(0)
            if k0 in dictionary:
                x = dictionary[k0]
                if isinstance(x, dict):
                    return self.get(key, default, x)
                else:
                    return x
            else:
                return default if default else None
        else:
            # single key
            if key in dictionary:
                return dictionary[key]
            else:
                return default if default else None
        
if __name__ == '__main__':
    _config = Config()

    # initial values
    logger.info("countdown: "+str(_config.get('countdown')))
    logger.info("[dppProxy][password]: "+str(_config.get(['dppProxy','password'])))

    # update
    _config.set("countdown", 809)
    _config.set(['dppProxy','password'], 'flerb')

    # modified values
    logger.info("countdown: "+str(_config.get('countdown')))
    logger.info("[dppProxy][password]: "+str(_config.get(['dppProxy','password'])))

    # fetch non-existent
    logger.info("aaa: "+str(_config.get('aaa')))
    logger.info("[bbb][ccc]: "+str(_config.get(['bbb','ccc'])))

    # fetch non-existent with defaults
    logger.info("aaa: "+str(_config.get('aaa', 'xyz')))
    logger.info("[bbb][ccc]: "+str(_config.get(['bbb','ccc'], 'tbd')))

    # insert new key value pairs
    _config.set("aaa", 888)
    _config.set(['bbb','ccc'], 'grimp')

    # fetch inserted values
    logger.info("aaa: "+str(_config.get('aaa')))
    logger.info("[bbb][ccc]: "+str(_config.get(['bbb','ccc'])))

    # dump JSON
    _config.dump(os.getenv("HOME")+"/dump.json")
    logger.info(_config.dump())

    logger.info("comcast: "+str(_config.get("comcast")))


