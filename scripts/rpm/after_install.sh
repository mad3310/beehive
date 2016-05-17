#!/bin/bash

chmod +x /etc/init.d/container-manager
chkconfig --add container-manager
/etc/init.d/container-manager start | stop | restart

exit 0
