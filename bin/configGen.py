#!/bin/python
# EMEA version
# 08/16/2016 - switch stack change
# 08/16/2016 - default-vars
# 01/10/2017 - rewrite to use netaddr
# 01/20/2017 - fix Tun200 WCmask
# 02/02/2017 - turn into method for testing
# 02/08/2017 - EMEA version
# 03/30/2017 - use Hostname for config file names
import time
import airspeed
import math
from netaddr import *
#
import os


#
# make changing templates easy
rt_template_4351='var_template-iwan-isr'
rt_template_4331='var_template-iwan-isr'
sw_template='var_template-ss-switch-emea'
#

# want to print extra stuff on the screen?
verbose = False
#
# show the dictionary when we are all done
def show(key=''):
    """
    list the vars dictionary
    """
    global var_dict
    if key != '':
        print (key,var_dict[key])
    else:
        for key,var in var_dict.items():
            print (key,var)

def get_varFile(desc,fid):
    """
    read vars file
    :param desc: describe type of vars
    :param fn: filename of var file
    """

    global var_dict
    #
    with open('%s' % (fid) ,'r') as finput:
      for line in finput:
        parms=line.strip().split('\t')
        if line[0]=='#': # lines starting with # are comments
            continue
        try:
            # eliminate spaces in parms
            var_dict[parms[0]]=parms[1].replace(" ",'_')
        except:
            print ('getvarfile/error:',desc,parms)
            continue
    finput.close()
    
def rtrConfig(varfile,region):
    from splitpfx import splitpfx
    dataPath = os.path.dirname(os.path.realpath(__file__)).replace('bin','data').replace('\\','/')+ '/' + region
    usrData = os.path.dirname(os.path.realpath(__file__)).replace('bin','usr').replace('\\','/')
    # initialize dictionary
    global var_dict
    var_dict = {}
    #########################
    # get defaults
    get_varFile('defaults','%s/%s' % (dataPath,'default-vars') )
    #########################
    # get system variables
    get_varFile('system','%s/%s' % (dataPath,'system-vars') )
    #########################

    get_varFile('site','%s/%s' % (usrData,varfile) )
    #
    # convert to integer for range operator
    if 'MPLS_Interface_Number_of_Links' in var_dict:
        var_dict['iMPLS_Interface_Number_of_Links'] = \
        int(var_dict['MPLS_Interface_Number_of_Links'])
    #
    # pick router template based on model
    # mask overrides value in site var file!!!
    if (var_dict['Router_Model']=='4331'):
        tmpl_file = '%s/%s' % (dataPath,rt_template_4331)


    else:
        tmpl_file = '%s/%s' % (dataPath,rt_template_4351)

    ipUser=IPNetwork( '%s/%s' % (var_dict['User_VLAN_Network'],var_dict['User_VLAN_Mask']))
    ipWireless=IPNetwork(var_dict['Wireless_VLAN_Network']+'/'+var_dict['Wireless_VLAN_Mask'])
    ipIPT=IPNetwork(var_dict['IPT_VLAN_Network']+'/'+var_dict['IPT_VLAN_Mask'])
    #
    # Make sure the networks are on network boundary
    # need CIDR in / format and WCmask in wildcard format
    # interface address is .1  of user,w/l, and IPT VLANs
    var_dict['User_VLAN_Network']=ipUser.network
    var_dict['User_VLAN_CIDR']=ipUser.cidr
    var_dict['User_VLAN_WCmask']=str(ipUser.network)+' '+ str(ipUser.hostmask)
    var_dict['User_VLAN_Address']=str(IPAddress(int(ipUser.network)+1))
    var_dict['User_VLAN_Pfx']=splitpfx(ipUser)
    
    var_dict['Wireless_VLAN_Network']=ipWireless.network
    var_dict['Wireless_VLAN_CIDR']=ipWireless.cidr
    var_dict['Wireless_VLAN_WCmask']=str(ipWireless.network) +' '+ str(ipWireless.hostmask)
    var_dict['Wireless_VLAN_Address']=str(IPAddress(int(ipWireless.network)+1))
    var_dict['Wireless_VLAN_Pfx']=splitpfx(ipWireless)
    var_dict['IP_VLAN_Network']=ipIPT.network
    var_dict['IPT_VLAN_CIDR']=ipIPT.cidr
    var_dict['IPT_VLAN_WCmask']=str(ipIPT.network) +' '+ str(ipIPT.hostmask)
    var_dict['IPT_VLAN_Address']=str(IPAddress(int(ipIPT.network)+1))
    var_dict['IPT_VLAN_Pfx']=splitpfx(ipIPT)
    #
    if var_dict['User2_VLAN_Number'] != 'NONE':
        print ('adding User2 Network',var_dict['User2_VLAN_Number'])
        ipUser2=IPNetwork(var_dict['User2_VLAN_Network']+'/'+var_dict['User2_VLAN_Mask'])
        var_dict['User2_VLAN_Network']=ipUser2.network
        var_dict['User2_VLAN_CIDR']=ipUser2.cidr
        var_dict['User2_VLAN_WCmask']=str(ipUser2.network) +' '+ str(ipUser2.hostmask)
        var_dict['User2_VLAN_Address']=str(IPAddress(int(ipUser2.network)+1))
        var_dict['User2_VLAN_Pfx']=splitpfx(ipUser2)
    if var_dict['Customer_VLAN_Number'] != 'NONE':
        print ('adding Customer Network',var_dict['Customer_VLAN_Number'])
        ipCustomer=IPNetwork(var_dict['Customer_VLAN_Network']+'/'+var_dict['Customer_VLAN_Mask'])
        var_dict['Customer_VLAN_Network']=ipCustomer.network
        var_dict['Customer_VLAN_CIDR']=ipCustomer.cidr
        var_dict['Customer_VLAN_WCmask']=str(ipCustomer.network) +' '+ str(ipCustomer.hostmask)
        var_dict['Customer_VLAN_Address']=str(IPAddress(int(ipCustomer.network)+1))
        var_dict['Customer_VLAN_Pfx']=splitpfx(ipCustomer)
    #
    if(var_dict['MPLS_Interface_Type']=='Frame'):
        var_dict['MPLS_Interface_Type']='frame'
    if(var_dict['MPLS_Interface_Type']=='Gi'):
        print ('* Note* Please use "Ethernet" for MPLS type instead of "Gi"')
        var_dict['MPLS_Interface_Type']='Ethernet'
    if(var_dict['MPLS_Interface_Type']=='Ethernet'):
        var_dict['MPLS_Interface']='GigabitEthernet0/0/1'
    elif(var_dict['MPLS_Interface_Type']=='frame'): # Frame-Relay always on Serial 0/0/3
        var_dict['MPLS_Interface']='Serial0/0/3:0.'+var_dict['FRAME_DLCI']
    elif(var_dict['MPLS_Interface_Type']=='mppp'):
        var_dict['MPLS_Interface']='Multilink123'
    else:
        var_dict['MPLS_Interface']='Unsupported'
        print ('* ERROR * MPLS interface not understood or program error')
    #
    # Have to code for speeds in .5 Mbps increments :-(
    if(var_dict['MPLS_Bandwidth']=='4500'):
        var_dict['MPLS_Speed']='4.5MBPS'
    elif(var_dict['MPLS_Bandwidth']=='1500'):
        var_dict['MPLS_Speed']='1.5MBPS'
    else:
        var_dict['MPLS_Speed']=str(int (int(var_dict['MPLS_Bandwidth'])/1000.) )+'MBPS'
    # Handle Tunnel Addresses
    ipTun100=IPNetwork(var_dict['Tunnel_100_Address']+'/'+var_dict['Tunnel_100_Mask'])
    ipTun200=IPNetwork(var_dict['Tunnel_200_Address']+'/'+var_dict['Tunnel_200_Mask'])
    #
    var_dict['Tunnel_100_Network']=ipTun100.cidr
    var_dict['Tunnel_200_Network']=ipTun200.cidr
    var_dict['Tunnel_100_WCmask']=str(var_dict['Tunnel_100_Network'].network) +' '+ str(var_dict['Tunnel_100_Network'].hostmask)
    var_dict['Tunnel_200_WCmask']=str(var_dict['Tunnel_200_Network'].network) +' '+ str(var_dict['Tunnel_200_Network'].hostmask)
    #
    if var_dict['Internet_BW_Down']=='':
        var_dict['Internet_BW_Down']=var_dict['Internet_Bandwidth']
    var_dict['Internet_Speed_Down']=str(int(var_dict['Internet_BW_Down' ])/1000)+'MBPS'
    #
    # x_BW is bandwidth in bps; x_Bandwidth is in Kbps
    var_dict['MPLS_BW']=var_dict['MPLS_Bandwidth']+'000'
    var_dict['Internet_BW']=var_dict['Internet_Bandwidth']+'000'
    #
    for i in range (1,8):
        try:
            ip = IPNetwork(var_dict[ eval("""'PUBLIC%s' % str(i)""")])
            var_dict[eval("""'PUBLIC%s_ADDR' % str(i)""")] = str(ip.ip)
            var_dict[eval("""'PUBLIC%s_WCmask' % str(i)""")] = str(ip.hostmask)
        except:
            break
    var_dict['Router']='01'
    nodeName = "%s_%s%s" %( var_dict['City'], "00000"[:5-len(var_dict['SiteNo'])],var_dict['SiteNo'])
    configName = '%s-R%s-cfg' % (nodeName,var_dict['Router'])
    config_output=open('%s/%s' % (usrData,configName) ,'w')
    rtrConfig=[configName]
    config_output.write('! Configuration generated: '+time.strftime("%Y-%m-%d %H:%M:%S")+'\n')
    config_output.write('! Template file: '+tmpl_file+'\n')
    #template=airspeed.Template( file(tmpl_file).read() )
    with open(tmpl_file) as tmpl:
            template=airspeed.Template( tmpl.read() )
    config_output.write(template.merge(var_dict))
    config_output.close()
    rtrConfig.append
    # create a 2nd config for DUAL router spoke site
    if (var_dict['SPOKE'] == 'DUAL'):
        var_dict['Router']='02'
        configName = '%s-R%s-cfg' % (nodeName,var_dict['Router'])
        config_output=open('%s/%s' % (usrData,configName) ,'w')
        rtrConfig.append(configName)
        # Preserve Border Master address
        var_dict['IWAN_MASTER']=var_dict['Router_Loopback']
        var_dict['Router_Loopback']=var_dict['Router_Loopback2']
        # Use next IP addr (.2) for interfaces
        var_dict['User_VLAN_IP']= str(IPAddress(int(IPAddress(var_dict['User_VLAN_Network'])+2)))
        var_dict['Wireless_VLAN_IP']=str(IPAddress(int(IPAddress(var_dict['Wireless_VLAN_Network'])+2)))
        var_dict['IPT_VLAN_IP']=str(IPAddress(int(IPAddress(var_dict['IPT_VLAN_Network'])+2)))
        config_output.write('! Configuration generated: '+time.strftime("%Y-%m-%d %H:%M:%S")+'\n')
        config_output.write('! Template file: '+tmpl_file+'\n')
        #template=airspeed.Template( file(tmpl_file).read() )
        with open(tmpl_file) as tmpl:
            template=airspeed.Template( tmpl.read() )
        config_output.write(template.merge(var_dict))
        config_output.close()

    return rtrConfig
    #
def swConfig(varfile,region):
    dataPath = os.path.dirname(os.path.realpath(__file__)).replace('bin','data').replace('\\','/')+ '/' + region
    usrData = os.path.dirname(os.path.realpath(__file__)).replace('bin','usr').replace('\\','/')
    ipUser=IPNetwork( '%s/%s' % (var_dict['User_VLAN_Network'], var_dict['User_VLAN_Mask']))
    # get switch mgmt address (.3) the standard is to use the .3 of the user network
    var_dict['Switch_Address'] = str(IPAddress(int(ipUser.network)+3))
    # does the switch use '_SS_' in its name to indicate switch stack
    var_dict['Switch_Stack_Size']=int(var_dict['Switch_Stack_Size'])
    var_dict['Switch_Stack']=[]
    for i in range (var_dict['Switch_Stack_Size']):
        var_dict['Switch_Stack'].append(str(i+1))
    if( int(var_dict['Switch_Stack_Size']) ) > 1:
        sStack='SS'
    else:
        sStack='S'
    # generate hostname of switch
    nodeName = "%s_%s%s" %( var_dict['City'], "00000"[:5-len(var_dict['SiteNo'])],var_dict['SiteNo'])
    var_dict['Switch_Hostname']= '%s_%s_%s' % (nodeName,sStack,'_01')
#
    swConfigName = '%s-swcfg' % (nodeName)
    sw_output=open('%s/%s' % (usrData,swConfigName),'w')
    swConfig = [swConfigName]
    sw_output.write('! SW Configuration generated: '+time.strftime("%Y-%m-%d %H:%M:%S")+'\n')
    #template=airspeed.Template( file('%s/%s' % (dataPath,sw_template) ).read() )
    with open('%s/%s' % (dataPath,sw_template) ) as tmpl:
            template=airspeed.Template( tmpl.read() )
    sw_output.write(template.merge(var_dict))
    sw_output.close()
    return swConfig

print (" type 'show()' to see the dictionary ")
def gen_config(vf):
    rtrConfig(vf,'na')
    swConfig (vf,'na')
if __name__ == '__main__':
    SiteNo=raw_input('site:').strip()
    gen_config ('%s-vars' % (SiteNo) )
