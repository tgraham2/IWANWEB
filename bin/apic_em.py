#!/usr/bin/env python

# apic_api provides ticket(), upload(filepath)
#
class apic_api(object):
    def __init__(self,srv,uid,pwd):
        self.base_url = "http://%s/api/v1/" % srv # 10.240.105.150
        self.user_data = {'username': uid, 'password': pwd}
        #print "APIC",uid,'@',self.base_url
        
    def ticket(self):
        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        ticket_url = self.base_url + "ticket"
        header = {'Content-Type' : 'application/json'}
        req = requests.post(ticket_url,json=self.user_data, headers = header, \
                   verify = False)
        #print "ticket:",req.reason
        if req.reason=='OK':
                r = req.json()
                return  r['response']['serviceTicket']
        else:
                #print req.reason
                return False

    def ckTask(self,tid):
        import requests
        header = {}
        ticket = self.ticket()
        if ticket:
                header['x-auth-token']=ticket
                url = self.base_url + "task/%s" % tid
                print("Task %s" % url)
                try:
                    response = requests.get(url,  headers=header, verify=False)
                except requests.exceptions.RequestException  as cerror:
                    print("Error processing request", cerror)
                    sys.exit(1)
                return response

    def get_config_id(self,config_name):
        import requests
        header = {}
        ticket = self.ticket()
        if ticket:
                header['x-auth-token']=ticket
                url = self.base_url + 'file/namespace/config'
                try:
                        response = requests.get(url, headers=header, verify=False)
                except requests.exceptions.RequestException  as cerror:
                        print("Error processing request", cerror)
                        sys.exit(1)
                #print response.json()
                r = response.json()['response']
                #print 'R:',r
                projid = 'notfound'
                for item in r:
                        #print 'ITEM:',item
                        if item["name"] == config_name:
                                config_id = item["id"]
                return config_id

    def get_project(self,projname):
        import requests
        header = {}
        ticket = self.ticket()
        if ticket:
                header['x-auth-token']=ticket
                url = self.base_url + 'pnp-project?offset=1'
                try:
                        response = requests.get(url, headers=header, verify=False)
                except requests.exceptions.RequestException  as cerror:
                        print("Error processing request", cerror)
                        sys.exit(1)
                #print response.json()
                r = response.json()['response']
                #print 'R:',r
                projid = 'notfound'
                for item in r:
                        #print 'ITEM:',item
                        if item["siteName"] == projname:
                                projid = item["id"]
                return projid

    def new_device(self,projid,device):
        import requests
        import json
        #print "ADDING:",device,'to',projid
        header={}
        header = {'Content-Type' : 'application/json'}
        ticket = self.ticket()
        if ticket:
                header['x-auth-token']=ticket
                url = self.base_url + 'pnp-project/' + projid + '/device'
                try:
                        response = requests.post(url, json=device , headers=header, verify=False)
                except requests.exceptions.RequestException  as cerror:
                        print("Error processing request", cerror)
                        sys.exit(1)
                #print response.json()
                r = response.json()['response']
                return r
            
    def upload(self,filepath):
        import requests
        import sys
        header = {}
        ticket = self.ticket()
        if ticket:
                header['x-auth-token']=ticket
                try:
                        f = open(filepath, "r")
                        files = {'fileUpload': f}
                except:
                        print("Could not open file %s" % filepath)
                        sys.exit(1)
                namespace = 'config'
                url = self.base_url + ("file/%s" % namespace)

                print("POST %s" % url)

                try:
                        response = requests.post(url, files=files, headers=header, verify=False)
                except requests.exceptions.RequestException  as cerror:
                        print("Error processing request", cerror)
                        sys.exit(1)
                #print response.json()
        else:
                response = {"error" : "could not obtain ticket"}
        return response
                
    def deleteConfig(self,configId):
        import requests
        import sys
        header = {}
        ticket = self.ticket()
        if ticket:
                header['x-auth-token']=ticket
                namespace = 'config'
                url = self.base_url + ("pnp-file/%s/%s" % (namespace,configId) )

                print("DELETE %s" % url)

                try:
                        response = requests.delete(url, headers=header, verify=False)
                        #print response.json()
                except requests.exceptions.RequestException  as cerror:
                        print("Error processing request", cerror)
                        sys.exit(1)
        else:
                response = {"error" : "could not obtain ticket"}

        return response

if __name__ == '__main__':
    apicAddr = "10.240.105.150"
    uid = "admin"
    pwd = "Jpoc16!!"
    from apic_em import apic_api
    import json
    apic = apic_api(apicAddr,uid,pwd)
    id=apic.get_project('demo')
    #print 'ID:',id
    device=[{
            "serialNumber":"FTX55500000",
            "platformId":"ISR4351/K9",
            "hostName":"host555" }]
    result = apic.new_device( id, device )
    #print result
