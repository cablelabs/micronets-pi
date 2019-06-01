# Test script to act as configurator (instead of iphone) by tapping on QRCode instead of scanning with iphone app
# Requires ethernet connection and the following defined in config.json:
# dppProxy: {
#	msoPortalUrl: <url>,	
#   username: <username>,
#   password: <password>,
#	deviceModelUID: <uid>	# This is used as the mud file identifier, eg: AgoNDQcDDgg
#}

def exec_dpp_onboard_proxy(config, uri, add_message):

	# Test for ethernet connection

	# 

def dpp_onboard_proxy(config, uri, add_message):
	try:
		exec_onboard_proxy(config, add_message)
	except Exception as e:
		add_message("!! {}".format(e.__doc__))
		print e.__doc__
		print e.message
		print '-'*60
        traceback.print_exc(file=sys.stdout)
        print '-'*60
