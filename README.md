This project aims to create a Command Line Interface to manage OESS. 

It allows you monitor links, switches and circuits and also to force reprovisioning 
   of a specific circuit, circuits using backup path or even all circuits. 
   Another possibility is change path from primary to backup or backup to primary of
   a specific circuit, all circuits using the backup path.

This tool was created having the Zabbix in mind, but as it exports info using JSON, any other NMS could be used.

Integration with Zabbix is available on http://www.sdn.amlight.net

Below is the embebed help:

<verbatim>
./oess_cli.py -l <url> -u <user> -p <pw> -g <group> [ -o <option> | -x <option> | -a <option>] 
    -l <url> or --url=<url>: URL for your OESS's installation (Default: https://localhost/oess/)
    -u <user> or --user=<user> : OESS' username (Default: user)
    -p <pw> or --password=<pw>: OESS' password (Default: password)
    -P or --Prompt: Prompts for password
    -g <group> or --group=<group>: OESS' workgroup (Default: admin)
    -o <option> or --monitoring-option=<option>, where <option> might be: (Default: 1)
         1 for monitor all nodes
         2 for monitor all links
         3 for monitor all circuits
    -t switch|link|circuit: Zabbix LLD: item to be monitored. Default (None)
    -z <1|2>: Zabbix LLD: (1) Count number of lines in each output or (2) list-only registers (0 is Neither)
     Do not use -t and -z at the same time. If you do, -z will be ignored
    -x <circuits|non_primary> [ -c link ] List All Circuits or Non-Primary Path Circuits [ -c filter for a specific link ]
    -a <reprovision|change_path> -b <circuit|non_primary|all>
         reprovision: forces the reprovisioning of a circuit, of all non_primary path circuits or all circuits
         change_path: change from Primary to Backup path or from Backup to Primary path. 
                Applies per circuit, for all non_primary or for all circuits
    Attention: -a requires an admin account and it will create DOWNTIME
</verbatim>

In case user decides no to user url, user, password or group, it could change the following variables in the script:

url='https://localhost/oess/'<BR>
user='user'<BR>
password='password'<BR>
group='admin'<BR>

A few examples:

Lists all switches:

./oess_cli.py -o 1
{"data":[{"switch1":2},
{"switch2":2},
{"switch3":2}]}

Lists all links:

./oess_cli.py -o 2
{"data":[{"switch1-switch2":2},
{"switch2-switch3":2}]}

List all circuits:
 
./oess_cli.py -o 3
{"data":[{"Vlan_100_Test1":2},
{"Vlan_101_Test2":2}]}

Params -t and -z are used for Zabbix integration and it will be explained on http://www.sdn.amlight.net
