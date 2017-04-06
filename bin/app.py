#!/usr/bin/env python3
# EMEA version
# enable debugging
import cgitb
cgitb.enable()
import os
realPath = os.path.dirname(__file__)
tmplPath = realPath.replace('\\','/').replace('bin','templates')
sessPath = realPath.replace('\\','/').replace('bin','sessions')
usrData = realPath.replace('\\','/').replace('bin','user')
global dataPath
import sys
print('PY:',sys.version.split()[0])
print ('path is %s' % realPath)
sys.path.append(realPath)
print ('version:%s' % sys.version)

def newtunnel(userid,pword): 
    global sdict
    if sdict['Region'][1] == 'NA': # stub for API call to InfoBlox
        return( ['100.100.100.100', '200.200.200.200'] )
    elif sdict['Region'][1] == 'EMEA':
        return ('10.244.124.%s' % str(sdict['SiteKey'][1]),'10.244.132.%s' % str(sdict['SiteKey'][1]))
    else:
        return ('0.0.0.0','0.0.0.0')
 
from configGen import rtrConfig
from configGen import swConfig
global rtrCnfFile, swCnfFile 
rtrCnfFile = []
swCnfFile = []
import web
from web import form
import airspeed
from netaddr import *
import requests
urls = (
        '/' , "Site", 
        "/local" , "Local" ,
        "/mpls", "MPLS",
        "/inet", "INET",
        "/edit", "EDIT",
        "/output", "WRITE",
        )
app = web.application(urls, globals())
application = app.wsgifunc()

web.config.debug = True

global session
if web.config.get('_session') is None:
    store = web.session.DiskStore(sessPath)
    init = {'room': None, 'count': 100}
    session = web.session.Session(app, store,  initializer=init)
    web.config._session = session
else:
    session = web.config._session
    
render = web.template.render(tmplPath,base='base') # template directory
global site_data, site_keys 
site_data = {
    'SiteNo':["Site Number","Enterprise Site Designation"],
    'City':["City","City (Site Location)"],
    'SiteKey':["Site Code","Key to generate Addressing"],
    'Region' : ["Region", "Location of Network (NA/EMEA)"],
    'SerialNo':["Router Serial No.","Chassis Serial Number for PNP"],
    'DC':["Datacenter Preference",'"Closest" Datacenter'],
    'MPLS_Type':["MPLS Handoff","Ethernet, MLPPP or Frame Relay"],
    'SpokeType':["Router Mode","Spoke has Single or Dual Routers"],
    'Router_Model':["Router Model","Router Model for PNP"],
    'AE_Project':["APIC-EM Project Name","Project Name APIC-EM for PNP"],
    'AE_Server': ["APIC-EM Server","APIC-EM Server for storing data"],
    'AE_UID': ["APID-EM User ID","User ID for storing data on APIC-EM"],
    'AE_PWD': ["APID-EM Password","APIC-EM password"]
    }
site_keys=["SiteNo","City","Region","SiteKey","SerialNo","DC","MPLS_Type","SpokeType","Router_Model", \
           "AE_Project", "AE_Server", "AE_UID", "AE_PWD"
           ]
global site_form
site_form = form.Form(
        form.Button("submit", description="Continue",action="/bin/app.py/local",method="POST",value="Enter Values"),
        form.Textbox("SiteNo",description="Site Number"),
        form.Textbox("City",description="City"),
        form.Radio('Region', ["NA","EMEA"], description="Network Locale", value="NA" ),
        form.Textbox("SiteKey",description="Key to generate Addressing",post="(EMEA only)"),
        form.Textbox("SerialNo",description="Router Serial No."),
        form.Radio('DC', ["DC1","DC2"], description="Datacenter Preference", value="DC1" ),
        form.Dropdown("MPLS_Type",description="MPLS Handoff", \
                      args=["Ethernet","MLPPP",("FrameRelay","Frame Relay")], value="Ethernet") ,
        form.Radio('SpokeType', ["SINGLE", "DUAL"], description="Spoke Router Mode", value="SINGLE" ),
        form.Dropdown("Router_Model",description="Router Model", \
                      args=["ISR4351/K9","ISR4331/K9","Other"], value="ISR4351/K9"),
        form.Textbox("AE_Project",description="APIC-EM Project Name", value="demo"),
        form.Dropdown("AE_Server", description="APIC-EM Server for saves", \
                      args = ["production","demo"], value="demo"),
        form.Textbox("AE_UID",description="APIC-EM User name",value="admin", ),
        form.Password("AE_PWD",description="APIC-EM Password",value="Jpoc16!!")
        )
apicProd = "10.48.110.151" 
apicDemo = "10.240.105.150"
global apic_em_uid, apic_em_pwd, apic_em_address
global nodeName
nodeName ='<node name>'
global sdict
sdict={} # OrderedDict()  # [key] [label,value,desc]
global x_dict
x_dict = {} # OrderedDict()
global x_keys
x_keys = []
global local_dict
global local_keys
local_keys=[]
local_dict={} # OrderedDict()
global m_dict
global m_keys
m_keys=[]
m_dict={} # OrderedDict()
global i_dict
global i_keys
i_keys=[]
i_dict={} # OrderedDict()
# flags - True means need to read defaults
global local_flag, m_flag, i_flag, x_flag
local_flag = True
m_flag = True
i_flag = True
x_flag = True
def get_data(parmfile,_dict,_keys):
    # parms:   0     1     2    3
    # keys:          0     1    2
    # dict is[key][label,value,desc]
    global dataPath
    with open('%s/%s' % (dataPath,parmfile), 'r' ) as fp:
        for line in fp:
            if line[0]=='#': # lines starting with # are comments
                continue
            parms=line.split('\t')
            label = parms[1]
            try:
                # eliminate spaces in parms
                value = parms[2].replace(" ",'_')
            except:
                value = parms[2]
            try:
                # get optional description
                desc = parms[3]
            except:
                desc = ' - - - '
            _keys.append(parms[0])
            _dict[parms[0]]=[label,value,desc]
        return False
    
class Site:
    def GET(self):
        global local_flag, m_flag, i_flag, x_flag
        global numRtr, numSw
        local_flag=True
        m_flag = True
        i_flag = True
        x_flag = True
        numRtr = 0
        numSw = 0
        # do $:f.render() in the template
        f = site_form()
        return render.site('Site Parameters', f)
    def POST(self):
        global sdict
        global nodeName
        global dataPath
        global apic_em_uid, apic_em_pwd, apic_em_address
        f = web.input()
        sdict = {} # OrderedDict()
        for element in site_keys:
            # [ label, value, description]
            sdict[element]=[site_data[element][0],f[element],site_data[element][1]]
            #print element,sdict[element]
        if (sdict['SiteKey'] != None) and (sdict['Region'][1]!='EMEA'):
            print ("Warning: Changing Region to EMEA")
            sdict['Region'][1]='EMEA'
        nodeName = "%s_%s%s" %( sdict['City'][1], "00000"[:5-len(sdict['SiteNo'][1])],sdict['SiteNo'][1])
        dataPath = realPath.replace('\\','/').replace('bin','data') + '/' + sdict['Region'][1].lower()
        print ("DP:",dataPath, sdict['Region'][1].lower() )
        print (sdict['City'])
        apic_em_uid = sdict['AE_UID'][1]
        sdict['AE_UID'][1] = '*' * 8
        apic_em_pwd = sdict['AE_PWD'][1]
        sdict['AE_PWD'][1] = '*' * 8
        if sdict['AE_Server'][1]=="production":
            apic_em_address = apicProd
        elif sdict['AE_Server'][1]=="demo":
            apic_em_address = apicDemo
        else:
            apic_em_address = "0.0.0.0"
        return render.showdata(nodeName,'Site','/local','/',sdict,site_keys)
class Local:
    def GET(self):
        global nodeName
        global local_dict
        global local_keys
        global local_flag
        if local_flag:
            local_dict={} # OrderedDict()
            local_keys=[]
            local_flag = get_data('local-data',local_dict,local_keys)
            tunAddr = newtunnel('x','y')
            local_dict['Tunnel_100_Address'][1]=tunAddr[0]
            local_dict['Tunnel_200_Address'][1]=tunAddr[1]
            if sdict['Region'][1] == 'EMEA': # setup addresses based on SiteKey
                local_dict['User_VLAN_Network'][1]= '10.180.%s.0' % str(sdict['SiteKey'][1])
                local_dict['Wireless_VLAN_Network'][1]= '10.180.%s.0' % str(1+int(sdict['SiteKey'][1]))
                local_dict['IPT_VLAN_Network'][1]= '10.182.%s.0' % str(sdict['SiteKey'][1])
                local_dict['Router_Loopback'][1]= '10.180.254.%s' % str(sdict['SiteKey'][1])
                local_dict['Router_Loopback2'][1]= str(IPAddress(local_dict['Router_Loopback'][1])+1)
            print ('Local:', local_dict)
            return render.data_form(nodeName,'Local','/local',local_dict,local_keys)
    
    def POST(self):
        global nodeName
        global local_dict
        global local_keys
        f = web.input()
        for element in local_dict:
            local_dict[element][1]=f[element] # who is splitting out the ' '.replace(' ','_')
        return render.showdata(nodeName,'Local','/mpls','/local',local_dict,local_keys)
class MPLS:
    def GET(self):
        global nodeName
        global sdict
        global m_dict
        global m_keys
        global m_flag
        if m_flag:
            m_dict={} # OrderedDict()
            m_keys=[]
            MPLS_Type = sdict['MPLS_Type'][1]
            #print 'MPLS:',MPLS_Type
            if MPLS_Type == 'Ethernet':
                mpls_data = 'mpls-e-data'
            elif MPLS_Type == 'FrameRelay':
                mpls_data = 'mpls-f-data'
            elif MPLS_Type == 'MLPPP':
                mpls_data = 'mpls-m-data'
            else:
                return('error MPLS/GET')
            m_flag = get_data(mpls_data,m_dict,m_keys)
        return render.data_form(nodeName,'MPLS','/mpls',m_dict,m_keys)
    
    def POST(self):
        global nodeName
        global m_dict
        global m_keys
        f = web.input()
        for element in m_keys:
            # [ label, value, description]
            m_dict[element][1]=f[element]
        print('MPLS:',m_dict)
        return render.showdata(nodeName,'MPLS','/inet','/mpls',m_dict,m_keys)
    
class INET:
    def GET(self):
        global nodeName
        global i_dict
        global i_keys
        global i_flag
        if i_flag:
            i_dict={} # OrderedDict()
            i_keys=[]
            i_flag=get_data('internet-data',i_dict,i_keys)
        return render.data_form(nodeName,'Internet','/inet',i_dict,i_keys)
    
    def POST(self):
        global nodeName
        global i_dict
        global i_keys
        f = web.input()
        for element in i_keys:
            # [ label, value, description]
            i_dict[element][1]=f[element]
        return render.showdata(nodeName,'Internet','/edit','/inet',i_dict,i_keys)
class EDIT:
    def GET(self):
        global nodeName
        global sdict
        global site_keys
        global local_dict
        global local_keys
        global m_dict
        global m_keys
        global i_dict
        global i_keys
        global x_keys
        global x_dict
        x_keys = site_keys + local_keys + m_keys + i_keys
        #x_dict = dict( sdict.items()+local_dict.items()+ m_dict.items()+i_dict.items() ) # python2
        #x_dict = { **sdict, **local_dict, **m_dict, **i_dict i} # python3
        for _dict in [sdict, local_dict, m_dict, i_dict]: # generic
            for element in _dict:
                x_dict[element] = _dict[element]
        return render.data_form(nodeName,'All data','/edit',x_dict, x_keys)
    
    def POST(self):
        global nodeName
        global x_keys
        global x_dict
        global x_flag
        f = web.input()
        for element in x_keys:
            # [ label, value, description]
            x_dict[element][1]=f[element]
        x_flag = True 
        return render.showdata(nodeName,'All data','/output','/edit',x_dict,x_keys)
class WRITE:
    
    def GET(self):
        from configGen import rtrConfig
        from configGen import swConfig
        global nodeName
        global usrData
        global x_keys
        global x_dict
        global x_flag
        global numRtr, numSw
        global rtrCnfFile, swCnfFile
        print ('/output',x_flag,x_dict['AE_Project'],rtrCnfFile,swCnfFile)
        if x_flag:
            rtrCnfFile = []
            swCnfFile = []
            x_flag = False
            # write local copy of vars file
            varFile = '%s-vars' % (nodeName)
            print ('Writing vars to %s/%s' % (usrData,varFile) )
            with open('%s/%s' % (usrData,varFile) , 'w') as fv:
                for key in x_keys:
                    fv.write('%s\t%s\n' % (key,x_dict[key][1] ) )
                fv.write('%s\t%s\n' % ('City',x_dict['City'][1] ) )
            # generate configuration
            if x_dict['Router_Gen'][1] == 'T':
                rtrCnfFile = rtrConfig(varFile,x_dict['Region'][1]) # gen_config returns list of config file names
            if x_dict['Switch_Gen'][1] == 'T':
                swCnfFile = swConfig(varFile,x_dict['Region'][1]) # gen_config returns list of config file names
            print ("R:",rtrCnfFile,)
            print ("S:",swCnfFile)
        return render.output_form(nodeName,x_dict['AE_Project'],rtrCnfFile,swCnfFile)
        #
    def POST(self):
        global nodeName
        global x_dict
        global apic_em_uid, apic_em_pwd, apic_em_address
        global rtrCnfFile, swCnfFile
        f = web.input()
        if f['choice'] == 'vars':
            varFile = '%s-vars' % (nodeName)
            # code for downloading file to desktop
            web.header("Content-Disposition", "attachment; filename=%s"  % varFile )
            web.header("Content-Type", "text/html")
            #web.header('Transfer-Encoding','chunked')
            #print "OPEN:",'%s/%s' % (usrData,varFile)
            f = open('%s/%s' % (usrData,varFile), 'rb')
            while 1:
                buf = f.read(1024 * 8)
                if not buf:
                    break
                yield buf
        elif f['choice'] == 'cfg':
            # code for downloading file to desktop
            web.header("Content-Disposition", "attachment; filename=%s"  % rtrCnfFile[0] )
            web.header("Content-Type", "text/html")
            #web.header('Transfer-Encoding','chunked')
            f = open('%s/%s' % (usrData,rtrCnfFile[0]), 'rb')
            while 1:
                buf = f.read(1024 * 8)
                if not buf:
                    break
                yield buf
        elif f['choice'] == 'cfg2':
            # code for downloading file to desktop
            web.header("Content-Disposition", "attachment; filename=%s"  % rtrCnfFile[1] )
            web.header("Content-Type", "text/html")
            #web.header('Transfer-Encoding','chunked')
            f = open('%s/%s' % (usrData,rtrCnfFile[1]), 'rb')
            while 1:
                buf = f.read(1024 * 8)
                if not buf:
                    break
                yield buf
        elif f['choice'] == 'swcfg':
            # code for downloading file to desktop
            web.header("Content-Disposition", "attachment; filename=%s"  % swCnfFile[0] )
            web.header("Content-Type", "text/html")
            #web.header('Transfer-Encoding','chunked')
            f = open('%s/%s' % (usrData,swCnfFile[0]), 'rb')
            while 1:
                buf = f.read(1024 * 8)
                if not buf:
                    break
                yield buf  
        elif f['choice'] == 'ae-vars':
            from apic_em import apic_api
            # upload vars file
            varFile = '%s-vars' % (nodeName)
            apic = apic_api(apic_em_address,apic_em_uid,apic_em_pwd)
            apic.upload('%s/%s' % (usrData,varFile) )
            cid = apic.get_config_id(varFile)
            print ('id for',varFile,'is',cid)
            raise web.seeother('/output')
        elif f['choice'] == 'ae-cfg':
            from apic_em import apic_api
            # upload configuration to project in APIC-EM
            # need to add code to support 2nd router
            cfgFile = '%sR01-cfg' % (nodeName)
            #print "using %s @ %s" % (apic_em_uid,apic_em_address)
            apic = apic_api(apic_em_address,apic_em_uid,apic_em_pwd)
            result = apic.upload('%s/%s' % (usrData,cfgFile))
            print (result.json())
            r = result.json()
            for item in r:
                print (item)
            for item in result:
                print (item)
            if r['response']['errorCode'] == 'FILE_ALREADY_EXISTS':
                cid = apic.get_config_id(cfgFile)
                #print 'id for',cfgFile,'is',cid
                result = apic.deleteConfig(cid)
                #print 'delete config:',result
                apic = apic_api(apic_em_address,apic_em_uid,apic_em_pwd)
                result = apic.upload('%s/%s' % (usrData,cfgFile))
                #print 'upload config2',result['response']
                #
            cid = apic.get_config_id(cfgFile)
            #print 'id for',cfgFile,'is',cid
            #print 'project:',x_dict['AE_Project'][1]
            pid = apic.get_project('demo')
            # create a new device in PnP
            device = [{
                "serialNumber":x_dict['SerialNo'][1],
                "configId":cid,
                "platformId":x_dict['Router_Model'][1],
                "hostName":"%s_%s_R_01" % (x_dict['City'][1],x_dict['SiteNo'][1])
                }]
            result = apic.new_device(pid, device )
            print ("NEWDEV:", result)
            raise web.seeother('/output')                      
        else:
            raise Exception('error WRITE/POST')
if __name__ == '__main__':
        app.run()
