#!/usr/bin/env python

'''
   This code was created to integrate OESS monitoring sub-system with Zabbix

   Created on: Jan/2015
   Author: Jeronimo / AMPATH

   TODO: Improve user's input validation

   Version 0.1
'''

import sys
import getopt
import time
import urllib2
import json
import getpass

# GLOBAL Variables - Local meaning
# Change this to reflect your scenario
# Remember: this is a security breach!!!!
# Use Read-Only password on OESS and protech this script if you add your password here

url='https://localhost/oess/'
user='user'
password='password'
group='admin'

# Default Values - Do not change unless you know what you are doing!
option='1'
count_output=0
target=''
admin_action=''
list=''
filter_link=''

# Errors Returned:
# 0 - Normal return, no error
# 1 - Unknown Workgroup
# 2 - Node informed doesn't exist
# 3 - User or password incorrect
# 4 - Wrong param inserted

def Usage():
   """ This funcion prints the Usage in case of errors or help needed.
       Always ends after printing this lines below.
   """
   print 'Usage: \n' + sys.argv[0] + ' -l <url> -u <user> -p <pw> -g <group> [ -o <option> | -x <option> | -a <option>] '
   print '\t-l <url> or --url=<url>: URL for your OESS\' installation (Default: ' + url + ')'
   print '\t-u <user> or --user=<user> : OESS\' username (Default: ' + user + ')'
   print '\t-p <pw> or --password=<pw>: OESS\' password (Default: ' + password + ')'
   print '\t-P or --Prompt: Prompts for password'
   print '\t-g <group> or --group=<group>: OESS\' workgroup (Default: ' + group + ')'
   print '\t-o <option> or --monitoring-option=<option>, where <option> might be: (Default: ' + option + ')'
   print '\t\t 1 for monitor all nodes'
   print '\t\t 2 for monitor all links'
   print '\t\t 3 for monitor all circuits'
   print '\t-t switch|link|circuit: Zabbix LLD: item to be monitored. Default (None)'
   print '\t-z <1|2>: Zabbix LLD: (1) Count number of lines in each output or (2) list-only registers (0 is Neither)'
   print '\t Do not use -t and -z at the same time. If you do, -z will be ignored'
   print '\t-x <circuits|non_primary> [ -c link ] List All Circuits or Non-Primary Path Circuits [ -c filter for a specific link ]'
   print '\t-a <reprovision|change_path> -b <circuit|non_primary|all>'
   print '\t\t reprovision: forces the reprovisioning of a circuit, of all non_primary path circuits or all circuits'
   print '\t\t change_path: change from Primary to Backup path or from Backup to Primary path. \n\t\t\t\tApplies per circuit, for all non_primary or for all circuits'
   print '\tAttention: -a requires an admin account and it will create DOWNTIME'
   sys.exit(0)

def get_data_from_oess_api(option,extra,target):
    """ This funcion prepares the URL to be sent to OESS API.
        Each URL is based on query (API file) and the action (what will be requested to OESS).
        Some requests might need more information, as target (switch to be monitored) or str (user's workgroup)
    """
    # Option 0 means get user's workgroup
    if option in ['0']:
        query, action = 'services/data.cgi?', 'action=get_workgroups'
    # Option 1 is related to nodes. Depending of target it might be look for one or all nodes
    elif option in ['1']:
        if target:
           query, action = 'services/monitoring.cgi?', 'action=get_node_status&node=' + target
        else:
           query, action = 'services/data.cgi?', 'action=get_all_node_status'
    # Option 2 is related to links
    elif option in ['2']:
        query, action = 'services/data.cgi?', 'action=get_all_link_status'
    # Option 3 is related to circuits
    elif option in ['3']:
        query, action = 'services/data.cgi?', 'action=get_existing_circuits&workgroup_id=' + str(extra)

    # Debug
    # print url + query + action

    # Send to OESS, returns a JSON reply
    tmp = urllib2.urlopen(url + query + action)
    tmp2 = tmp.read()
    jsonData = json.loads(tmp2)
    try:
        # If no error, return results
        return jsonData['results']
    except:
        # If the node informed by user doesn't exist, return it
        print 'Unknown Target: ' + target
        sys.exit(2)

# Authenticate to OESS
def oess_authenticate(url,user,pw,wg):
    """ Authenticate against OESS using HTTPBasicAuth
        Returns the Working Group ID
        Creates a opener for future queries
    """
    # create a password manager
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

    # Add the username and password.
    password_mgr.add_password(None, url, user, pw)
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)

    # create "opener" (OpenerDirector instance)
    opener = urllib2.build_opener(handler)

    try:
        # use the opener to fetch a URL
        opener.open(url)
    except:
        print 'ERROR: User or Password Incorrect.'
        sys.exit(3)

    # Install the opener.
    # Now all calls to urllib2.urlopen use our opener.
    urllib2.install_opener(opener)

    # Extract the WG_ID from the json output and return it
    searchResults = get_data_from_oess_api('0','0','0')

    for er in searchResults:
       if er['name'] == wg:
         wg_id = er['workgroup_id']
         return wg_id

    print 'Unknown Workgroup: ' + wg
    sys.exit(1)

def print_count_output(searchResults,lines_result):
    """ Funcion create to only print the amount of lines. It's used by Zabbix LLD
    """
    print lines_result

def print_list(searchResults,lines_result,option):
    """ Funcion create to print a list of node, link or circuits in a JSON format. It's used by Zabbix LLD
    """
    if not lines_result:
       print '0'
       return '0'
    er = searchResults[0]
    if option in ['1']:
       id = "{#OFSW}"
    elif option in ['2']:
       id = "{#LINK}"
    elif option in ['3']:
       id = "{#CIRCUIT}"

    count = 0
    for er in searchResults:
       # Useful to create a generic procedure ahead
       if option in ['1']:
          name = er["name"]
       elif option in ['2']:
          name = er["name"]
       elif option in ['3']:
          name = er["description"]

       # If count = 0 and lines_results > 1 -> Means that we have to use ','
       if not count and lines_result > 1:
          print '{"data":[' + json.dumps( { id : name }, separators=(',',':')) + ','
       # If count = 0 and lines_result = 0 -> Means one entry only
       elif not count and lines_result:
          print '{"data":[' + json.dumps( { id : name }, separators=(',',':'))
       # Not first output, no need to print {"data":[
       count = count + 1
       if count > 1 and count != lines_result:
          print json.dumps( { id : name }, separators=(',',':')) + ','
       elif count > 1 and count == lines_result:
          print json.dumps( { id : name }, separators=(',',':')) + ']}'


def print_error(option):
    """ Function create to print errors
    """
    if option in ['1']:
       print 'No switches configured or error to fetch them'
    elif option in ['2']:
       print 'No links configured or error to fetch them'
    elif option in ['3']:
       print 'No circuits configured or error to fetch them'

def check_state(option,er):
    """ Used for monitoring. Get data from OESS to identify the current status of 1) node, 2) link or 3) circuit. It's used mainly by Zabbix LLD.
    """
    if option in ['1']:
       #print 'check_state option 1'
       if er["operational_state"] in ['up']:
           return er["name"],2
       elif er["operational_state"] in ['down']:
           return er["name"],1
       else:
           return er["name"],0
    elif option in ['2']:
       if er["status"] in ['up']:
           return er["name"],2
       elif er["status"] in ['down']:
           return er["name"],1
       else:
           return er["name"],0
    elif option in ['3']:
       if er["operational_state"] in ['down']:
           return er["description"],0
       elif er["active_path"] in ['primary']:
           return er["description"],2
       elif er["active_path"] in ['backup']:
           return er["description"],1
       else:
           return er["description"],0

def print_target_results(searchResults,option,target):
    """ Filter for one specific target (one node, one link or one circuit)
        Used mainly for Zabbix LLD
    """
    if option in ['1']:
        print searchResults["status"]
    elif option in ['2']:
       for er in searchResults:
           if er["name"] in target:
              name, status = check_state(option,er)
              print status
              break
    elif option in ['3']:
       for er in searchResults:
           if er["description"] in target:
              name, status = check_state(option,er)
              print status
              break


def get_status(wg_id,count_output,option,target):
    """ Fetch for option (node, links, circuits)
    """
    searchResults = get_data_from_oess_api(option,wg_id,target)

    # Print only 'name' and  'operational_state' in a JSON format

    if target:
       # Print just the status of the target
       print_target_results(searchResults,option,target)

    elif count_output in ['1']:
       # Count amount of items - Zabbix LLD
       print_count_output(searchResults,len(searchResults))

    elif count_output in ['2']:
       # List in JSON format. Don't show status! - Zabbix LLD
       print_list(searchResults,len(searchResults),option)

       # no result?
    elif not len(searchResults):
       print_error(option)

       # For normal people, normal results in JSON (not that normal, right?)
    else:
       count = 0
       lines_result = len(searchResults)
       for er in searchResults:
          # Convert "operational_state" from "up" or "down" to 1 or 0
          name, status = check_state(option,er)

          # If count = 0 and lines_results > 1 -> Means that we have to use ','
          if not count and lines_result > 1:
             print '{"data":[' + json.dumps( { name : status }, separators=(',',':')) + ','
          # If count = 0 and lines_result = 0 -> Means one entry only
          elif not count and lines_result:
             print '{"data":[' + json.dumps( { name : status }, separators=(',',':'))
          # Not first output, no need to print {"data":[
          count = count + 1
          if count > 1 and count != lines_result:
             print json.dumps( { name : status }, separators=(',',':')) + ','
          elif count > 1 and count == lines_result:
             print json.dumps( { name : status }, separators=(',',':')) + ']}'


def list_circuits(wg_id,list,filter_circuit):
    '''
    '''
    option='3'
    searchResults = get_data_from_oess_api(option,wg_id,target)

    for er in searchResults:
        if list in ['circuits']:
            if filter_circuit:
               path = er["active_path"]
               try:
                  if path in ["primary"]:
                      # If there is a circuit with no link, except: pass
                      ids = er["links"]
                  else:
                      ids = er["backup_links"]
                  for er2 in ids:
                      if er2["name"] == filter_circuit:
                          print er["description"]
                          break
               except:
                  pass
            else:
               print er["description"]
        else:
            name, status = check_state(option,er)
            # 2 means the Primary Path, 0 is down
            if status != 2 and status != 0:
               print er["description"]


def oess_provision_api(instruction,wg_id,c_id,name):
    """
    # services/provisioning.cgi
    # fail_over_circuit : requires circuit_id and workgroup_id
    # reprovision_circuit: requires circuit_id and workgroup_id
    # instruction should be fail_over or reprovision
    """
    query, action = 'services/provisioning.cgi?', 'action=' + instruction + '_circuit&workgroup_id=' + str(wg_id) + '&circuit_id=' + str(c_id)

    tmp = urllib2.urlopen(url + query + action)
    tmp2 = tmp.read()
    jsonData = json.loads(tmp2)
    try:
        if jsonData['results']:
           print instruction + ' for circuit ' + name + ' performed with success'
    except:
        print 'Error for ' + instruction + ' for circuit ' + name + ': ' + jsonData['error']


def Admin_action(wg_id,admin_action,target):
    ''' This function is to be used for admin activities. Or force reprovision or force to change the path (Primary -> Backup or vice-versa)
        User has to insert the desired action
    '''
    option='3'
    searchResults = get_data_from_oess_api(option,wg_id,target)
    found=0
    for er in searchResults:
       if target in ['non_primary']:
           # check if it is using backup then get the circuit_id
           if er['active_path'] in ['backup']:
              oess_provision_api(admin_action,wg_id,er['circuit_id'],er['description'])
       elif target in ['all']:
           # get the circuit_id
           oess_provision_api(admin_action,wg_id,er['circuit_id'],er['description'])
       else:
           if er["description"] == target:
                # reprovision circuit 'target'
                # get the circuit_id
                oess_provision_api(admin_action,wg_id,er['circuit_id'],er['description'])
                found=1
    if not found and target not in ['non_primary','all']:
       print 'Circuit ' + target + ' does not exist'


# Main

# Handle all input params
letters = 'l:u:p:g:o:t:a:x:b:c:z:hP'
keywords = ['url=','user=','password=','group=','option=','target=','admin=','help','list=','Prompt']

try:
   opts, extraparams = getopt.getopt(sys.argv[1:],letters,keywords)
except getopt.GetoptError as err:
   print str(err)
   Usage()
   sys.exit("4")

for o,p in opts:
   if o in ['-l','--url']:
      url = p
   elif o in ['-u','--user']:
      user = p
   elif o in ['-p','--password']:
      password= p
   elif o in ['-g','--group']:
      group = p
   elif o in ['-o','--option']:
      if p not in ['1','2','3','4']:
         print 'Use <option> as 1, 2, 3 or 4'
         sys.exit(4)
      else:
         option = p
   elif o in ['-t','--target']:
      target = p
   elif o in ['-h','--help']:
      Usage()
   elif o in ['-z']:
      count_output= p
   elif o in ['-x']:
      if p in ['circuits','non_primary']:
         list = p
      else:
         print 'Use -x with "circuits" or "non_primary"'
         sys.exit(4)
   elif o in ['-c']:
         if not list:
            print 'Use -c with -x'
         else:
            filter_link = p
   elif o in ['-a','--admin']:
      if p in ['change_path']:
         admin_action = 'fail_over'
      elif p in ['reprovision']:
         admin_action = 'reprovision'
      else:
         print 'Use <option> as "reprovision" or "change_path"'
         sys.exit(4)
   elif o in ['-b']:
         target = p
   elif o in ['-P','--Prompt','--prompt']:
         try:
             password = getpass.getpass()
         except:
             sys.exit(4)
   else:
         Usage()
         sys.exit(4)

# Debug
#print 'URL: ',url
#print 'User:',user
#print 'Pass:',password
#print 'Group:',group
#print 'Option:',option

# Authenticate and receive the workgroup id
wg_id = oess_authenticate(url,user,password,group)

# if list variable is set, using -x just list circuits accordingly to the filter (circuits = all or non_primary = circuits not using the primary path (default for list is empty))
if list:
  list_circuits(wg_id,list,filter_link)
# Else if admin_action is set (-a or --admin) go to the Admin_action function. It's used for reprovision or change_path from Primary to Backup or from Backup to Primary
elif admin_action:
  Admin_action(wg_id,admin_action,target)
# If it's no to list or an admin action go here
else:
  get_status(wg_id,count_output,option,target)

sys.exit(0)
