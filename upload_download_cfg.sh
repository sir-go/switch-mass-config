#!/bin/sh

#======================== upload\download config
wct=$1              # write comunity
sw_ip=$2            # switch ip
srv_ip=$3           # tftp server ip
conf_name=$4'.cfg'  # config_name

sleep 5
# set server ip
snmpset -v2c -c ${wct} ${sw_ip} 1.3.6.1.4.1.171.12.1.2.1.1.3.3 a ${srv_ip}
#
## set channel for upload/download (2 = network-load)
snmpset -v2c -c ${wct} ${sw_ip} 1.3.6.1.4.1.171.12.1.2.1.1.4.3 i 2
#
## set config_file name
snmpset -v2c -c ${wct} ${sw_ip} 1.3.6.1.4.1.171.12.1.2.1.1.5.3 s ${conf_name}
#
## operation type (2 = upload, 3 = download)
snmpset -v2c -c ${wct} ${sw_ip} 1.3.6.1.4.1.171.12.1.2.1.1.7.3 i 2
##snmpset -v2c -c ${wct} ${sw_ip} 1.3.6.1.4.1.171.12.1.2.1.1.7.3 i 3
#
## beginning operation (3 = start)
snmpset -v2c -c ${wct} ${sw_ip} 1.3.6.1.4.1.171.12.1.2.1.1.8.3 i 3
#
## save settings
sleep 3
snmpset -v2c -c ${wct} ${sw_ip} 1.3.6.1.4.1.171.12.1.2.6.0 i 5
