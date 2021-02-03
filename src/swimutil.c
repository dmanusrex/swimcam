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


/* FIXME: A quick solution from various sources, refactor to use
          the GLib/GObject libraries instead and make it 
          fully IPV6 aware */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <arpa/inet.h>
#include <glib.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <stdio.h>
#include "swimutil.h"

/* Convert a network address to text */

#define DEFAULT_MASTER_PORT 54545

char *get_ip_str (struct sockaddr_in *sa, char *s, size_t maxlen);

char *
get_ip_str (struct sockaddr_in *sa, char *s, size_t maxlen)
{
  switch (sa->sin_family) {
    case AF_INET:
      inet_ntop (AF_INET, &(((struct sockaddr_in *) sa)->sin_addr), s, maxlen);
      break;

    case AF_INET6:
      inet_ntop (AF_INET6, &(((struct sockaddr_in6 *) sa)->sin6_addr),
          s, maxlen);
      break;

    default:
      strncpy (s, "Unknown AF", maxlen);
      return NULL;
  }

  return s;
}


gchar *
wait_for_core (void)
{
  gint server_fd;
  struct sockaddr_in address;
  gint opt = 1;
  gint addrlen = sizeof (address);
  gchar s[40];
  gchar buffer[2048] = { 0 };

  if ((server_fd = socket (AF_INET, SOCK_DGRAM, 0)) == 0) {
    perror ("socket failed");
    exit (EXIT_FAILURE);
  }

  if (setsockopt (server_fd, SOL_SOCKET, SO_REUSEPORT | SO_REUSEADDR,
          &opt, sizeof (opt))) {
    perror ("setsockopt");
    exit (EXIT_FAILURE);
  }

  address.sin_family = AF_INET;
  address.sin_addr.s_addr = INADDR_ANY;
  address.sin_port = htons (DEFAULT_MASTER_PORT);

  if (bind (server_fd, (struct sockaddr *) &address, sizeof (address)) < 0) {
    perror ("bind failed");
    exit (EXIT_FAILURE);
  }

  if ((recvfrom (server_fd, buffer, 2048, opt,
              (struct sockaddr *) &address, (socklen_t *) & addrlen)) < 0) {
    perror ("accept");
    exit (EXIT_FAILURE);
  }

  get_ip_str (&address, s, sizeof (s));

  return g_strdup (s);

}
