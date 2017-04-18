#!/usr/bin/env python
from netaddr import *
#
def splitpfx(ip):
    subnets = []
    nw = IPNetwork( '%s/%s' % (IPNetwork( ip ).network,IPNetwork( ip ).netmask) )
    #
    if nw.prefixlen >= 28:
        subnets.append(str(nw))
        return subnets
    elif nw.prefixlen == 21:
        jend = 128
    elif nw.prefixlen == 22:
        jend = 64
    elif nw.prefixlen == 23:
        jend = 32
    elif nw.prefixlen == 24:
        jend = 16
    elif nw.prefixlen == 26:
        jend = 4
    else:
        print (nw, 'not supported')
        return None
    #

    for j in range (0,jend):
        x = IPNetwork('0.0.0.0')
        x.prefixlen = 28
        x.value = int(nw.ip) + (j*16)
        subnets.append(str(x))
    return subnets
#
if __name__ == "__main__":
    for i in ['10.10.10.32/28','10.10.10.1/26','10.10.10.200/24','10.10.10.0/23', \
              '10.10.10.0/22','10.10.10.0/21']:
        x = splitpfx(i)
        print (i, x[0:10])
    
