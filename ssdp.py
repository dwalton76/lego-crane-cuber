#!/usr/bin/env python2

import argparse
import logging
import re
import select
import socket
import subprocess
import struct
import sys
from pprint import pformat
from httplib import HTTPResponse
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO

log = logging.getLogger(__name__)

MCAST_GRP = '239.255.255.250'
MCAST_PORT = 1900


# ===========
# SSDP Client
# ===========
def interface_addresses():
    """
    Return a list of all IPv4 addresses (ignore 127.0.0.1)
    """

    '''
    1: lo    inet 127.0.0.1/8 scope host lo\       valid_lft forever
    1: lo    inet6 ::1/128 scope host \       valid_lft forever prefer
    3: wlan2    inet 192.168.0.27/24 brd 192.168.0.255 scope global wlan2
    3: wlan2    inet6 2606:a000:4547:3100:20f:55ff:febc:1266/64 scope gl
    3: wlan2    inet6 fe80::20f:55ff:febc:1266/64 scope link \       va
    '''
    result = []

    for line in subprocess.check_output(['ip', '-o', 'addr', 'show']).decode('ascii').splitlines():
        re_line = re.search('^\d+: \S+\s+inet (\d+\.\d+\.\d+\.\d+)\/\d+', line)

        if re_line:
            ip = str(re_line.group(1))
            if ip != '127.0.0.1':
                result.append(ip)

    return result


class Response(HTTPResponse):

    def __init__(self, response_text):
        self.fp = StringIO(response_text)
        self.debuglevel = 0
        self.strict = 0
        self.msg = None
        self._method = None
        self.begin()


DISCOVERY_MSG = ('M-SEARCH * HTTP/1.1\r\n' +
                 'ST: %(library)s:%(service)s\r\n' +
                 'MX: 3\r\n' +
                 'MAN: "ssdp:discover"\r\n' +
                 'HOST: 239.255.255.250:1900\r\n\r\n')


def client(library_to_query, service_to_query, timeout=1, retries=1):
    socket.setdefaulttimeout(timeout)
    ip_addrs = interface_addresses()

    for attempt_index in xrange(retries):
        for addr in ip_addrs:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.bind((addr, 0))

            msg = DISCOVERY_MSG % dict(service=service_to_query, library=library_to_query)
            sock.sendto(msg, (MCAST_GRP, MCAST_PORT))

            try:
                data = sock.recv(1024)
            except socket.timeout:
                pass
            else:
                response = Response(data)
                return str(response.getheader('Location'))
    return None


# ===========
# SSDP Server
# ===========
LOCATION_MSG = ('HTTP/1.1 200 OK\r\n' +
                'ST: %(library)s:%(service)s\r\n'
                'USN: %(service)s\r\n'
                'Location: %(loc)s\r\n'
                'Cache-Control: max-age=900\r\n\r\n')


class Request(BaseHTTPRequestHandler):

    def __init__(self, request_text):
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message


def server(library_to_serve, services_to_serve, timeout=5):
    log.info("SSDP server running for the '%s' library, services %s" %\
             (library_to_serve, pformat(services_to_serve)))

    socket.setdefaulttimeout(timeout)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.bind(('', MCAST_PORT))

    mreq = struct.pack('4sl', socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:

        # Wait for data for 1 sec.  We stop after 1s in case we RXed a SIGTERM
        (readable, writeable, exceptional) = select.select([sock], [], [], 1)

        for s in readable:
            (data, addr) = sock.recvfrom(4096)

            request = Request(data)
            if not request.error_code and \
                    request.command == 'M-SEARCH' and \
                    request.path == '*' and \
                    request.headers['ST'].startswith(library_to_serve) and \
                    request.headers['MAN'] == '"ssdp:discover"':

                service = request.headers['ST'].split(':', 2)[1]
                if service in services_to_serve:
                    loc = services_to_serve[service]
                    log.info("RXed request for service %s, location is %s" % (service, loc))
                    msg = LOCATION_MSG % dict(service=service, loc=loc, library=library_to_serve)
                    sock.sendto(msg, addr)
                else:
                    log.info("RXed request for unnsupported service %s" % service)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)5s: %(message)s')

    # Color the errors and warnings in red
    logging.addLevelName(logging.ERROR, "\033[91m  %s\033[0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.WARNING, "\033[91m%s\033[0m" % logging.getLevelName(logging.WARNING))
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="SSDP client/server in python")
    parser.add_argument('action', choices=('client', 'server'))
    parser.add_argument('-l', '--library', type=str, default='ev3')
    parser.add_argument('-s', '--services', type=str)
    args = parser.parse_args()

    SERVICE_LOCS = {'id1': '127.0.0.1:7711',
                    'id2': '127.0.0.1:7722'}

    if args.action == 'client':
        result = client(args.library, 'id1')
        print result

        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        server(args.library, SERVICE_LOCS)
