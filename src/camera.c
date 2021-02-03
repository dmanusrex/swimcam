/* SwimCam - Synchronized racing camera system
 * Copyright (C) 2020-2021 Darren Richer <darren.richer@gmail.com>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Affero General Public
 * License as published by the Free Software Foundation; either
 * version 3 of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License along with this program; if not, 
 * see <https://www.gnu.org/licenses/> 
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include "swimutil.h"

#include <arpa/inet.h>
#include <gst/gst.h>
#include <gst/rtsp-server/rtsp-server.h>
#include <locale.h>
#include <netinet/in.h>
#include <mosquitto.h>
/* FIXME: Add signal handling #include <signal.h> */
#include <sys/socket.h>
#include <stdio.h>


#define DEFAULT_RACE_RUNNING FALSE
#define DEFAULT_DATETIME_FORMAT "%F %T.%f"      /* YYYY-MM-DD hh:mm:ss.ff */
#define DEFAULT_MASTER_PORT 54545
#define DEFAULT_MQTT_PORT 1883
#define DEFAULT_TZ_OFFSET -5

typedef struct _SwimCamRaceInfo SwimCamRaceInfo;

/* SwimCamRaceInfo:State tracking */

struct _SwimCamRaceInfo
{
  /* Configuration and state Info */
  gchar *core_ip;
  GstRTSPMedia *sharedmedia;
  GstElement *textoverlay;

  /* Race Information */
  gboolean race_running;
  gchar *datetime_format;
  GstClockTime race_basetime;
  gchar *race_info_text;
  gint  left_lane_number;
  gint  right_lane_number;

  /* Test/Debug Information */
  gboolean race_test_mode;
  guint frame_counter;
};

/* Command line options */
/* FIXME: Most of this will be deprecated with central config */

static gint swimcam_instance = 1;
static gint swimcam_left_lane = 1;
static gint swimcam_right_lane = 2;
static gboolean add_frame_counter = FALSE;
static gboolean ignore_master = FALSE;
static gboolean enable_daemon = FALSE;

gchar *pipeline =  (gchar *) "( videotestsrc is-live=true "
                   "! video/x-raw,width=320,height=240,framerate=30/1 "
                   "! textoverlay name=race ! x264enc tune=zerolatency "
                   "! rtph264pay name=pay0 pt=96 )";

static GOptionEntry entries[] = {
  {"instance", 'i', 0, G_OPTION_ARG_INT, &swimcam_instance, "Camera Instance #",
        "N"},
  {"frames", 'f', 0, G_OPTION_ARG_NONE, &add_frame_counter,
        "Add a frame counter", NULL},
  {"master", 'm', 0, G_OPTION_ARG_NONE, &ignore_master,
        "Running on master server, force localhost", NULL},
  {"daemon", 'd', 0, G_OPTION_ARG_NONE, &enable_daemon, "Run as a daemon"},
  {"pipeline", 'p', 0, G_OPTION_ARG_STRING, &pipeline,
        "Override pipeline from config", NULL},
  {"left", 'l', 0, G_OPTION_ARG_INT, &swimcam_left_lane, 
        "Lane # on left [0=Not Used](default 1)", NULL},
  {"right", 'r', 0, G_OPTION_ARG_INT, &swimcam_right_lane,
        "Lane # on right [0=Not Used] (default 2)", NULL},
  {NULL}
};

void connect_callback (struct mosquitto *mosq, void *obj, int result);
void message_callback (struct mosquitto *mosq, void *obj,
    const struct mosquitto_message *message);


static gchar *
gst_race_overlay_render_time (GstClockTime time, guint tzoffset)
{
  guint hours, mins, secs, msecs;

  if (!GST_CLOCK_TIME_IS_VALID (time))
    return g_strdup ("");

  hours = (guint) (time / (GST_SECOND * 60 * 60));
  hours = (hours + tzoffset) % 24;
  mins = (guint) ((time / (GST_SECOND * 60)) % 60);
  secs = (guint) ((time / GST_SECOND) % 60);
  msecs = (guint) ((time % GST_SECOND) / (1000 * 1000));

  return g_strdup_printf ("%02u:%02u:%02u.%03u", hours, mins, secs, msecs);
}

/* FIXME: Check thread safety between mosquitto and
          PadProbe callback on the raceinfo struct */

static GstPadProbeReturn
race_overlay_callback (GstPad * pad,
    GstPadProbeInfo * info, SwimCamRaceInfo * raceinfo)
{
  GstBuffer *buffer;
  gchar *walltime_str, *racetime_str, *txt, *tmp;
  GstClockTime ts_base, ts_buffer, walltime, racetime;
  GstElement *parent;

  buffer = GST_PAD_PROBE_INFO_BUFFER (info);

  if (buffer == NULL) {
    return GST_PAD_PROBE_OK;
  }

  ts_buffer = GST_BUFFER_TIMESTAMP (buffer);

  if (!GST_CLOCK_TIME_IS_VALID (ts_buffer)) {
    GST_DEBUG ("buffer without valid timestamp");
    return GST_PAD_PROBE_OK;
  }

  GST_DEBUG ("buffer with timestamp %" GST_TIME_FORMAT,
      GST_TIME_ARGS (ts_buffer));

  ts_base = gst_rtsp_media_get_base_time (raceinfo->sharedmedia);

  if (ts_base == GST_CLOCK_TIME_NONE) {
    GST_DEBUG ("media without valid base time timestamp");
    return GST_PAD_PROBE_OK;
  }

  /* FIXME:
   *  These are all live streams and, consequently, only 1 segment
   *  Fix this later to handle all use cases
   *  (Watch for segment signals, track and use segment_to_running_time) */

  walltime = ts_base + ts_buffer;
  walltime_str = gst_race_overlay_render_time (walltime, -5);

  if (raceinfo->race_running) {
    if (raceinfo->race_basetime < ts_base) {
      racetime_str = g_strdup_printf ("Waiting for start...");
    } else {
      racetime = walltime - raceinfo->race_basetime;
      tmp = gst_race_overlay_render_time (racetime, 0);
      racetime_str = g_strdup_printf ("%s %s", tmp, raceinfo->race_info_text);
      g_free (tmp);
    }
  } else {
    racetime_str = g_strdup_printf ("Waiting for start...");
  }

  parent = gst_pad_get_parent_element (pad);

  if (raceinfo->race_test_mode) {
    raceinfo->frame_counter += 1;
    txt = g_strdup_printf ("%s\n%s\nTest Frame # %u",
        walltime_str, racetime_str, raceinfo->frame_counter);
  } else {
    txt = g_strdup_printf ("%s\n%s", walltime_str, racetime_str);
  }

  g_object_set (parent, "text", txt, NULL);

  g_free (walltime_str);
  g_free (racetime_str);
  g_free (txt);

  return GST_PAD_PROBE_OK;

}

/* called when a new media pipeline is constructed. 
 * We find the textoverlay element and attach the pad probe */
static void
media_configure (GstRTSPMediaFactory * factory, GstRTSPMedia * media,
    SwimCamRaceInfo * raceinfo)
{
  GstElement *element, *txtsrc;
  GstPad *pad;

  /* get the element used for providing the streams of the media */
  element = gst_rtsp_media_get_element (media);
  raceinfo->sharedmedia = media;

  /* get the textoverlay element, 
     it should be named 'race' with the name property
     and add our pad probe */
  txtsrc = gst_bin_get_by_name_recurse_up (GST_BIN (element), "race");

  if (!txtsrc) {
    g_print ("textoverlay for raceinfo not found... did you tag it?\n");
  } else {
    g_object_set (txtsrc,
        "valignment", 2,
        "halignment", 0,
        "line-alignment", 0,
        "shaded-background", TRUE,
        "shading-value", 250, "font-desc", "Monospace", NULL);
    pad = gst_element_get_static_pad (txtsrc, "video_sink");
    raceinfo->textoverlay = txtsrc;
    gst_pad_add_probe (pad, GST_PAD_PROBE_TYPE_BUFFER,
        (GstPadProbeCallback) race_overlay_callback, raceinfo, NULL);
    gst_object_unref (pad);
  }

  gst_object_unref (txtsrc);
  gst_object_unref (element);
}

void
connect_callback (struct mosquitto *mosq, void *obj, int result)
{

  if (result) {
    g_print ("Connection to MQTT broker failed\n");
    exit (1);
  }

  if (mosquitto_subscribe (mosq, NULL, "swimcam/start", 0)) {
    g_print ("Unable to subscribe to starter messages\n");
    exit (1);
  }

}

void
message_callback (struct mosquitto *mosq, void *obj,
    const struct mosquitto_message *message)
{
  gchar **msg_parts;
  SwimCamRaceInfo *info;
  guint64 temptime;
  GError *errorcode = NULL;

  GST_DEBUG ("got message '%.*s' for topic '%s'\n", message->payloadlen,
      (char *) message->payload, message->topic);

  msg_parts = g_strsplit (message->payload, "|", 0);

  if (g_strv_length (msg_parts) == 0) {
    GST_DEBUG ("Invalid starter message");
    g_strfreev (msg_parts);
    return;
  }

  info = (SwimCamRaceInfo *) obj;
  /* TODO: Add names from the the start list */

  if (g_str_has_prefix (msg_parts[0], "START")) {
    if (g_ascii_string_to_unsigned (msg_parts[1], 10, 0, G_MAXUINT64, &temptime,
            &errorcode)) {
      info->race_basetime = temptime;
      info->race_running = TRUE;
      g_free (info->race_info_text);
      info->race_info_text = g_strdup_printf ("%s", msg_parts[2]);
    } else {
      GST_DEBUG ("Start Time Conversion Failure");
      g_free (info->race_info_text);
      info->race_info_text =
          g_strdup_printf ("Invalid Start Command Received...");
      info->race_running = FALSE;
    }
  } else {
    g_free (info->race_info_text);
    info->race_info_text = g_strdup_printf ("Waiting for start...");
    info->race_running = FALSE;
  }
  g_strfreev (msg_parts);
}

static void
daemonize (void)
{
  int ret;

  ret = fork ();
  if (ret < 0)
    exit (1);                   /* fork error */
  if (ret > 0)
    exit (0);                   /* parent */

  /* FIXME: Add some signal handling */
  /* signal (SIGHUP, do_quit); */
  /* signal (SIGTERM, do_quit); */
}

int
main (int argc, char *argv[])
{
  SwimCamRaceInfo *raceinfo;
  GMainLoop *loop;
  GstRTSPServer *server;
  GstRTSPMountPoints *mounts;
  GstRTSPMediaFactory *factory;
  GstClock *net_clock;
  GOptionContext *context;
  GError *error = NULL;
  gchar *clientid = NULL;
  struct mosquitto *mosq;
  int rc = 0;

  setlocale (LC_ALL, "");
  context = g_option_context_new ("SwimCam Racing Camera");
  g_option_context_add_main_entries (context, entries, NULL);
  g_option_context_add_group (context, gst_init_get_option_group ());
  g_option_context_set_help_enabled (context, TRUE);
  if (!g_option_context_parse (context, &argc, &argv, &error)) {
    g_print ("option parsing failed: %s\n", error->message);
    exit (1);
  }
  g_option_context_free (context);

  if ((swimcam_left_lane < 0) || (swimcam_left_lane > 12)) {
     g_print ("Left lane parameter must be between 0 and 12\n");
     exit (1);
  }

  if ((swimcam_right_lane < 0) || (swimcam_right_lane > 12)) {
     g_print ("Right lane parameter must be between 0 and 12\n");
     exit (1);
  }

  
  /* FIXME: Add interrupt signal handler */
  /* signal (SIGINT, signal_interrupt); */

  /* Daemonize before initializing GStreamer or the Mosquitto Library */
  if (enable_daemon)
    daemonize ();

  /* Initialize GStreamer */
  gst_init (&argc, &argv);

  /* Setup our global state */
  raceinfo = g_new0 (SwimCamRaceInfo, 1);

  raceinfo->race_running = DEFAULT_RACE_RUNNING;
  raceinfo->datetime_format = g_strdup (DEFAULT_DATETIME_FORMAT);
  raceinfo->race_basetime = GST_CLOCK_TIME_NONE;
  raceinfo->race_test_mode = add_frame_counter;
  raceinfo->race_info_text = g_strdup ("Waiting for start...");
  raceinfo->frame_counter = 0;
  raceinfo->left_lane_number = swimcam_left_lane;
  raceinfo->right_lane_number = swimcam_right_lane;

  /* Wait for the network core (config server, timing source, etc) */
  if (ignore_master)
    raceinfo->core_ip = strdup ("127.0.0.1");
  else
    raceinfo->core_ip = wait_for_core ();
  GST_INFO ("Core IP: %s\n", raceinfo->core_ip);

  /* MQTT for configuration and camera synchronization
   * 
   * Topic: /SwimCam/start - Starter Messages
   *        /SwimCam/config/clientID - Configuration Data */

  mosquitto_lib_init ();

  /* Enable receipt of start commands via MQTT */
  clientid = g_strdup_printf ("%s-%d", g_get_host_name (), swimcam_instance);
  GST_INFO ("MQTT clientid: %s", clientid);
  mosq = mosquitto_new (clientid, true, raceinfo);

  if (mosq == NULL) {
    GST_ERROR ("failed to initialize MQTT\n");
    mosquitto_lib_cleanup ();
    exit (1);
  }

  /* TODO: local config file for Mosquitto credentials */
  mosquitto_username_pw_set (mosq, "swimcam", "swimming");
  mosquitto_connect_callback_set (mosq, connect_callback);
  mosquitto_message_callback_set (mosq, message_callback);

  rc = mosquitto_connect_async (mosq, raceinfo->core_ip, DEFAULT_MQTT_PORT, 60);

  if (rc) {
    GST_ERROR ("MQTT connect broker error\n");
    mosquitto_destroy (mosq);
    mosquitto_lib_cleanup ();
    exit (1);
  }

  rc = mosquitto_loop_start (mosq);

  if (rc) {
    GST_ERROR ("MQTT failed to start loop\n");
    mosquitto_destroy (mosq);
    mosquitto_lib_cleanup ();
    exit (1);
  }

  /* Get the Network Clock */
  net_clock = gst_net_client_clock_new ("net_clock",
      raceinfo->core_ip, 9998, 0);

  if (net_clock == NULL) {
    GST_ERROR ("Failed to create net clock client for %s:%d\n",
        raceinfo->core_ip, 9998);
    return 1;
  }

  /* Wait for the clock to stabilise */
  gst_clock_wait_for_sync (net_clock, GST_CLOCK_TIME_NONE);

  loop = g_main_loop_new (NULL, FALSE);

  /* create & configure a server instance */
  server = gst_rtsp_server_new ();
  mounts = gst_rtsp_server_get_mount_points (server);

  /* This media factory can use any launch line. 
   * Restrictions:
   *    output elements must be named pay%d.
   *    textoverlay element should be named "race" to trigger
   *       the race information overlay
   *    the launch line must be binned. Just put () around it */

  factory = gst_rtsp_media_factory_new ();
  gst_rtsp_media_factory_set_shared (factory, TRUE);
  gst_rtsp_media_factory_set_clock (factory, net_clock);
  gst_rtsp_media_factory_set_launch (factory, pipeline);

  g_signal_connect (factory, "media-configure", (GCallback) media_configure,
      raceinfo);
  gst_rtsp_mount_points_add_factory (mounts, "/swimcam", factory);
  g_object_unref (mounts);
  gst_rtsp_server_attach (server, NULL);

  /* start serving */
  g_print ("stream ready at rtsp://127.0.0.1:8554/swimcam\n");

  g_main_loop_run (loop);

  /* FIXME: Need to do more cleanup */
  mosquitto_loop_stop (mosq, false);
  mosquitto_destroy (mosq);
  mosquitto_lib_cleanup ();

  return 0;
}
