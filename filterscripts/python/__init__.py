from icecube import icetray
try:
	# this fails if ROOT_FOUND or BUILD_ASTRO are false
	icetray.load("filterscripts", False)
except:
	pass

del icetray
