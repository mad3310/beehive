#!/bin/bash

chmod +x /etc/init.d/beehive
chkconfig --add beehive
/etc/init.d/beehive start | stop | restart

exit 0
