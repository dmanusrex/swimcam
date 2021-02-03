srcs = [
   'camera.c',
   'swimutil.c'
]

hdrs = [
   'swimutil.h'
]

executable('camera', srcs, hdrs,
    dependencies : [glib_deps, gst_dep, gstapp_dep, gstnet_dep,gstrtspserver_dep,mosquitto_dep],
    install: false)


