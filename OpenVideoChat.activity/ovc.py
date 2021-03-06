#    This file is part of OpenVideoChat.
#
#    OpenVideoChat is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    OpenVideoChat is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with OpenVideoChat.  If not, see <http://www.gnu.org/licenses/>.
"""
:mod: `OpenVideoChat/OpenVideoChat.activity/ovc` -- Open Video Chat
=======================================================================

.. moduleauthor:: Justin Lewis <jlew.blackout@gmail.com>
.. moduleauthor:: Taylor Rose <tjr1351@rit.edu>
.. moduleauthor:: Fran Rogers <fran@dumetella.net>
.. moduleauthor:: Remy DeCausemaker <remyd@civx.us>
.. moduleauthor:: Luke Macken <lmacken@redhat.com>
.. moduleauthor:: Casey DeLorme <cxd4280@rit.edu>
"""


#External Imports
import logger
import fcntl
import array
import socket
import struct
from sugar3 import profile
from gettext import gettext as _
from sugar3.graphics.alert import NotifyAlert
from sugar3.activity.activity import Activity
from gi.repository import GObject


# Define Logger for Logging
logger = logging.getLogger('ovc-activity')


#Local Imports
from gui import Gui
from gst_stack import GSTStack
from network_stack import NetworkStack


# Temporary Constants
RECEIVING_STREAM = False


class OpenVideoChatActivity(Activity):

    def __init__(self, handle):
        Activity.__init__(self, handle)

        # Self-Enforced max_participants
        self.max_participants = 2

        # Revise logical checks to shared_activity flags and remove these:
        if self.shared_activity:
            self.sent_ip = 1
        else:
            self.sent_ip = 2


        ###########
        # Setup Gui
        ###########
        self.set_canvas(Gui(self))


        #####################
        # Setup Network Stack
        #####################
        # self.netstack = NetworkStack(self)
        # self._sh_hnd = self.connect('shared', self.netstack.shared_cb)
        # self._jo_hnd = self.connect('joined', self.netstack.joined_cb)

        #################
        # Setup Pipeline
        #################
        print "Setting up GStreamer"
        self.gststack = GSTStack(self.get_canvas().render_preview, self.get_canvas().render_incoming)
        self.gststack.build_preview()
        self.gststack.build_incoming_pipeline()
        GObject.idle_add(self.gststack.start_stop_incoming_pipeline, True)

    def can_close(self):
        print "Closing, stopping pipelines"
        self.gststack.start_stop_incoming_pipeline(False)
        self.gststack.start_stop_outgoing_pipeline(False)
        return True

    def _alert(self, title, text=None, timeout=5):
        alert = NotifyAlert(timeout=timeout)
        alert.props.title = title
        alert.props.msg = text
        self.add_alert(alert)
        alert.connect('response', self._alert_cancel_cb)
        alert.show()

    def _alert_cancel_cb(self, alert, response_id):
        self.remove_alert(alert)

    # def net_cb(self, src, args):
    #     """
    #     Callback for network commands
    #     """

    #     # new chat message
    #     if src == "chat":
    #         message, sender = args
    #         self.get_canvas().receive_message(message)

    #     # join request
    #     elif src == "join":
    #         handle = self.netstack.get_tube_handle()
    #         if handle and self.sent_ip > 0:
    #             # http://code.activestate.com/recipes/439094-get-the-ip-address
    #             # -associated-with-a-network-inter/

    #             def get_ip_address(ifname):
    #                 s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #                 return socket.inet_ntoa(fcntl.ioctl(
    #                         s.fileno(),
    #                         0x8915,  # SIOCGIFADDR
    #                         struct.pack('256s', ifname[:15]))[20:24])

    #             # http://code.activestate.com/recipes/439093-get-names-of-all-
    #             # up-network-interfaces-linux-only/

    #             def all_interfaces():
    #                 max_possible = 128  # arbitrary. raise if needed.
    #                 bytes = max_possible * 32
    #                 s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #                 names = array.array('B', '\0' * bytes)
    #                 outbytes = struct.unpack('iL', fcntl.ioctl(
    #                     s.fileno(),
    #                     0x8912,  # SIOCGIFCONF
    #                     struct.pack('iL', bytes, names.buffer_info()[0])))[0]
    #                 namestr = names.tostring()
    #                 return [namestr[i:i + 32].split('\0', 1)[0] for i in range
    #                                                 (0, outbytes, 32)]


    #             for interface in all_interfaces():
    #                 if interface != 'lo':
    #                     try:
    #                         ip = get_ip_address(interface)
    #                         self.sent_ip = self.sent_ip - 1
    #                         handle.announce_ip(ip)
    #                         break
    #                     except:
    #                         print "Interface %s did not give ip" % interface
    #             else:
    #                 print "Could not find ip address"

    #     elif src == "ip":

    #         # fixme: Store ip with user so we can make user lists to switch
    #         # between later on

    #         if not hasattr(self, 'out'):
    #                 #~ s1,s2,s3 = self.out.get_state()
    #                 #~ if s2 == gst.STATE_PLAYING:
    #                 #~ print args,"has sent its ip, ignoring as we are already
    #                 #              streaming"
    #                 #~ else:

    #             self.gststack.build_outgoing_pipeline(args)

    #             # FIXME
    #             GObject.timeout_add(5000, self.gststack.start_stop_outgoing_pipeline)

    #         else:
    #             print args, "has sent its ip, ignoring as we are already \
    #                         streaming"

    #     elif src == "buddy_add":
    #         self.get_canvas().receive_message(_("%s has joined the chat") % args)

    #     elif src == "buddy_rem":
    #         self.get_canvas().receive_message(_("%s has left the chat") % args)

    # # Send new chat message
    # def send_message(self, text):
    #     handle = self.netstack.get_tube_handle()
    #     prof = profile.get_nick_name()

    #     if handle:
    #         handle.receive_message("<%s> %s" % (prof, text))

    def get_stream(self):
        return RECEIVING_STREAM

    def send_stream(self):
        self.get_canvas().run_toggles()

    # Save Chat Log to History
    def write_file(self, file_path):
        file = open(file_path, 'w')
        file.write(self.get_canvas().get_history())
        file.close()

    # Load Chat Log from History
    def read_file(self, file_path):
        file = open(file_path, 'r')
        self.get_canvas().receive_message(file.read())
        file.close()
