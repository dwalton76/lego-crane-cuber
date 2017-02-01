#!/usr/bin/env python2

import re
import select
import socket
import subprocess
import struct
import sys
from httplib import HTTPResponse
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO

LIB_ID = 'my_library'
MCAST_GRP = '239.255.255.250'
MCAST_PORT = 1900
SERVICE_LOCS = {'id1': '127.0.0.1:7766', 'id2': '127.0.0.1:7766'}

DISCOVERY_MSG = ('M-SEARCH * HTTP/1.1\r\n' +
                 'ST: %(library)s:%(service)s\r\n' +
                 'MX: 3\r\n' +
                 'MAN: "ssdp:discover"\r\n' +
                 'HOST: 239.255.255.250:1900\r\n\r\n')

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


class Response(HTTPResponse):

    def __init__(self, response_text):
        self.fp = StringIO(response_text)
        self.debuglevel = 0
        self.strict = 0
        self.msg = None
        self._method = None
        self.begin()


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


def client(timeout=1, retries=5):
    socket.setdefaulttimeout(timeout)

    for _ in xrange(retries):
        for addr in interface_addresses():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.bind((addr, 0))

            msg = DISCOVERY_MSG % dict(service='id1', library=LIB_ID)
            for _ in xrange(2):
                # sending it more than once will
                # decrease the probability of a timeout
                sock.sendto(msg, (MCAST_GRP, MCAST_PORT))

            try:
                data = sock.recv(1024)
            except socket.timeout:
                pass
            else:
                response = Response(data)
                print(response.getheader('Location'))
                return


def server(timeout=5):

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
                    request.headers['ST'].startswith(LIB_ID) and \
                    request.headers['MAN'] == '"ssdp:discover"':

                service = request.headers['ST'].split(':', 2)[1]
                if service in SERVICE_LOCS:
                    loc = SERVICE_LOCS[service]
                    msg = LOCATION_MSG % dict(service=service, loc=loc, library=LIB_ID)
                    sock.sendto(msg, addr)

if __name__ == '__main__':
    if len(sys.argv) > 1 and 'client' in sys.argv[1]:
        client()
    else:
        server()
