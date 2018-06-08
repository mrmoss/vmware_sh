# Introduction
Don't like powercli/powershell?

Do you need to do something with vSphere and you're like `"T_T, I have to get on a Windows VM..."`?

Do you wish administrating vSphere stuff was a bit more like bash?

Wish you could just make a shell script to manage vSphere (because EVERYTHING, including 90's embedded MIPS security cameras, supports shell scripts...but not Windows)?

Look no further?

In all honesty...there are probably better scripts out there than these...use at your own risk...I tried to make everything pretty solid in terms of error handling and such...but I'm sure I messed something up somewhere...

# Installation
There's not really an install process here, you simply need python3, pyvim, and pyvmomi.

With most not-Windows systems you can install python (if it isn't already installed) like so:

`sudo PACKAGE-MANAGER install python3 #Where package manager is something like brew, apt, apt-get, etc...`

To install the two modules, you can maybe even do this on Windows (but should you?):

`sudo pip install pyvim pyvmomi`

That's it.

# Todo
1. vm-migrate
2. vm-permission-ls
3. vm-permission-add
4. vm-permission-rm
5. vm-ifconfig-ls
6. vm-ifconfig-mv
7. vm-ifconfig-rm

# Usage examples
## Standard usage
```
./vm-X -h - show help
./vm-X -p PASSWORD_FILE - Use this file to lookup usernames and passwords.

Example password file:
mike@vc.example.com,123456seven
mike@vc.example2.com,rootpass
```

## Show all datastore info
```
./vm-datacenter-df mike@vc.example.com
Attempting to connect as "mike" to "vc.example.com"...
	Password:
	Connected

Alpha Datacenter
         Datastore Capacity   Free   Used %Used
ds-alpha-san0-vms0   2198Gi  176Gi 2022Gi   91%
ds-alpha-san0-vms1   2198Gi  399Gi 1799Gi   81%
ds-alpha-san0-vms2   2198Gi  397Gi 1801Gi   81%

Bravo Datacenter
         Datastore Capacity   Free   Used %Used
ds-bravo-san1-vms0   2198Gi  176Gi 2022Gi   91%
ds-bravo-san1-vms1   2198Gi  399Gi 1799Gi   81%
ds-bravo-san1-vms2   2198Gi  397Gi 1801Gi   81%
```

## Show all datastore info for datastores in the 'Alpha Datacenter'
```
./vm-datacenter-df mike@vc.example.com 'Alpha Datacenter'
Attempting to connect as "mike" to "vc.example.com"...
	Password:
	Connected

Alpha Datacenter
         Datastore Capacity   Free   Used %Used
ds-alpha-san0-vms0   2198Gi  176Gi 2022Gi   91%
ds-alpha-san0-vms1   2198Gi  399Gi 1799Gi   81%
ds-alpha-san0-vms2   2198Gi  397Gi 1801Gi   81%
```

## Show clusters and hosts for all datacenters
```
./vm-datacenter-ls mike@vc.example.com
Attempting to connect as "mike" to "vc.example.com"...
	Password:
	Connected

Alpha Datacenter
	Alpha Cluster
		vs0.alpha.example.com
		vs1.alpha.example.com
		vs2.alpha.example.com
Bravo Datacenter
	Bravo Cluster
		vs0.bravo.example.com
		vs1.bravo.example.com
		vs2.bravo.example.com
```

## Show clusters and hosts in the 'Bravo Datacenter'
```
./vm-datacenter-ls mike@vc.example.com Bravo\ Datacenter
Attempting to connect as "mike" to "vc.example.com"...
	Password:
	Connected

Bravo Datacenter
	Bravo Cluster
		vs0.bravo.example.com
		vs1.bravo.example.com
		vs2.bravo.example.com
```

## Show all network info for all hosts
```
./vm-network-ls mike@vc.example.com
Attempting to connect as "mike" to "vc.example.com"...
	Password:
	Connected

vs0.alpha.example.com
	NETWORK_1
	NETWORK_2
	NETWORK_3

vs1.alpha.example.com
	NETWORK_1
	NETWORK_2
	NETWORK_3

...
```

## Show all network info for the given two hosts
```
./vm-network-ls mike@vc.example.com vs2.bravo.example.com vs0.alpha.example.com
Attempting to connect as "mike" to "vc.example.com"...
	Password:
	Connected

vs2.bravo.example.com
	NETWORK_1
	NETWORK_2
	NETWORK_3

vs0.alpha.example.com
	NETWORK_1
	NETWORK_2
	NETWORK_3
```

## Poweroff the two given VMs
```
./vm-poweroff mike@vc.example.com Alpha\ Datacenter/base/windows/w7 Alpha\ Datacenter/base/windows/w10
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Powering off "/Alpha Datacenter/base/windows/w7"...done
Powering off "/Alpha Datacenter/base/windows/w10"...done
```

## Poweron the two given VMs
```
./vm-poweron mike@vc.example.com Alpha\ Datacenter/base/linux/arch Alpha\ Datacenter/base/linux/ubuntu
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Powering on "/Alpha Datacenter/base/linux/arch"...done
Powering on "/Alpha Datacenter/base/linux/ubuntu"...done
```

## List all top-level structures in the server root (aka, datacenters)
```
./vm-ls mike@vc.example.com
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Alpha Datacenter
Bravo Datacenter
```

## List all top-level structures in the given two paths
```
./vm-ls mike@vc.example.com Alpha\ Datacenter Bravo\ Datacenter
Attempting to connect as "mike" to "vc.example.com"...
	Connected

/Alpha Datacenter:
base
main-ad

/Bravo Datacenter:
base
```

## List all top-level folder-structures in the given path
```
./vm-ls -f mike@vc.example.com Alpha\ Datacenter
Attempting to connect as "mike" to "vc.example.com"...
	Connected

base
```

## List all top-level vm-structures in the given path
```
./vm-ls -m mike@vc.example.com Alpha\ Datacenter
Attempting to connect as "mike" to "vc.example.com"...
	Connected

main-ad
```

## List all top-level structures in the given two paths
```
./vm-ls mike@vc.example.com Alpha\ Datacenter/base/linux Alpha\ Datacenter/base/windows
Attempting to connect as "mike" to "vc.example.com"...
	Connected

/Alpha Datacenter/base/linux:
arch
centos
fedora
ubuntu

/Alpha Datacenter/base/windows:
w7
w8
w8.1
w10
w95
w98
wxp
```

## List all top-level structures in the given two paths with full paths
```
./vm-ls -l mike@vc.example.com Alpha\ Datacenter/base/linux Alpha\ Datacenter/base/windows
Attempting to connect as "mike" to "vc.example.com"...
	Connected

/Alpha Datacenter/base/linux:
/Alpha Datacenter/base/linux/arch
/Alpha Datacenter/base/linux/centos
/Alpha Datacenter/base/linux/fedora
/Alpha Datacenter/base/linux/ubuntu

/Alpha Datacenter/base/windows:
/Alpha Datacenter/base/windows/w7
/Alpha Datacenter/base/windows/w8
/Alpha Datacenter/base/windows/w8.1
/Alpha Datacenter/base/windows/w10
/Alpha Datacenter/base/windows/w95
/Alpha Datacenter/base/windows/w98
/Alpha Datacenter/base/windows/wxp
```

## List all top-level vm-structures in the given two paths with full paths and remove the "labels"
```
./vm-ls -lmn mike@vc.example.com Alpha\ Datacenter/base/linux Alpha\ Datacenter/base/windows
Attempting to connect as "mike" to "vc.example.com"...
	Connected

/Alpha Datacenter/base/linux/arch
/Alpha Datacenter/base/linux/centos
/Alpha Datacenter/base/linux/fedora
/Alpha Datacenter/base/linux/ubuntu
/Alpha Datacenter/base/windows/w7
/Alpha Datacenter/base/windows/w8
/Alpha Datacenter/base/windows/w8.1
/Alpha Datacenter/base/windows/w10
/Alpha Datacenter/base/windows/w95
/Alpha Datacenter/base/windows/w98
/Alpha Datacenter/base/windows/wxp
```

## Rename Alpha Datacenter/base/windows/w7 to Alpha Datacenter/base/windows/w7-test
```
./vm-mv mike@vc.example.com 'Alpha Datacenter/base/windows/w7' 'Alpha Datacenter/base/windows/w7-test'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Renaming to "/Alpha Datacenter/base/windows/w7-test"...success
```

## Move Alpha Datacenter/base/windows/w7-test to Alpha Datacenter/w7-test
```
./vm-mv mike@vc.example.com 'Alpha Datacenter/base/windows/w7-test' 'Alpha Datacenter/w7-test'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Moving to "/Alpha Datacenter/w7-test"...success
```

## Move Alpha Datacenter/w7-test to Alpha Datacenter/base/windows/w7
```
./vm-mv mike@vc.example.com 'Alpha Datacenter/w7-test' 'Alpha Datacenter/base/windows/w7'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Temporarily renaming to "/Alpha Datacenter/LYJVZEGUMYGVT29KW3DYCUYXNY7NZT"...success
Moving to "/Alpha Datacenter/base/windows/LYJVZEGUMYGVT29KW3DYCUYXNY7NZT"...success
Renaming to "/Alpha Datacenter/base/windows/w7"...success
```

## Create a new snapshot on Alpha Datacenter/base/linux/arch named "Test Snapshot"
```
./vm-snapshot mike@vc.example.com 'Alpha Datacenter/base/linux/arch' 'Test Snapshot'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Creating snapshot "Test Snapshot" on "/Alpha Datacenter/base/linux/arch"...success
```

## List snapshots of Alpha Datacenter/base/linux/arch and Alpha Datacenter/base/linux/centos (note the second set of entries)
```
./vm-snapshot-ls mike@vc.example.com 'Alpha Datacenter/base/linux/arch' 'Alpha Datacenter/base/linux/centos'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

/Alpha Datacenter/base/linux/arch:
No snapshots found.

/Alpha Datacenter/base/linux/centos:
[0]	/Base Snapshot
[1]	/Base Snapshot/Experiment 1
[2]	/Base Snapshot/Experiment 2
[3]	/Base Snapshot/Experiment 1
```

## Revert to snapshot via index
```
./vm-snapshot-revert mike@vc.example.com 'Alpha Datacenter/base/linux/arch' -n 2
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Reverting "/Alpha Datacenter/base/linux/arch" to snapshot "/Base Snapshot/Experiment 2"...success
```

## Revert to snapshot via name
```
./vm-snapshot-revert mike@vc.example.com 'Alpha Datacenter/base/linux/arch' 'Base Snapshot'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Reverting "/Alpha Datacenter/base/linux/arch" to snapshot "/Base Snapshot"...success
```

## Remove snapshot via index
```
./vm-snapshot-rm mike@vc.example.com 'Alpha Datacenter/base/linux/arch' -n 2
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Removing snapshot "/Base Snapshot/Experiment 2" from "/Alpha Datacenter/base/linux/arch"...success
```

## Remove snapshot via name (and all duplicates of that name)
```
./vm-snapshot-rm -d mike@vc.example.com 'Alpha Datacenter/base/linux/arch' 'Base Snapshot/Experiment 1'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Removing snapshot "/Base Snapshot/Experiment 1" from "/Alpha Datacenter/base/linux/arch"...success
Removing snapshot "/Base Snapshot/Experiment 1" from "/Alpha Datacenter/base/linux/arch"...success
```

## Remove snapshot and all children
```
./vm-snapshot-rm -r mike@vc.example.com 'Alpha Datacenter/base/linux/arch' 'Base Snapshot'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Removing snapshot "/Base Snapshot" from "/Alpha Datacenter/base/linux/arch"...success
```

## Copy virtual machine
```
./vm-cp mike@vc.example.com 'Alpha Datacenter/base/linux/arch' 'Alpha Datacenter/arch-test1'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Cloning "/Alpha Datacenter/base/linux/arch" to "/Alpha Datacenter/arch-test1"...success
```

## Copy virtual machine to a different host
```
./vm-cp mike@vc.example.com 'Alpha Datacenter/base/linux/arch' 'Alpha Datacenter/arch-test2' --to-host vs2.alpha.example.com
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Cloning "/Alpha Datacenter/base/linux/arch" to "/Alpha Datacenter/arch-test2"...success
```

## Copy virtual machine from a snapshot name
```
./vm-cp mike@vc.example.com 'Alpha Datacenter/base/linux/centos' 'Alpha Datacenter/centos-test1' -s 'Base Snapshot/Experiment 2'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Cloning "/Alpha Datacenter/base/linux/centos" to "/Alpha Datacenter/centos-test1"...success
```

## Copy virtual machine from a snapshot index
```
./vm-cp mike@vc.example.com 'Alpha Datacenter/base/linux/centos' 'Alpha Datacenter/centos-test2' -n -s 1
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Cloning "/Alpha Datacenter/base/linux/centos" to "/Alpha Datacenter/centos-test2"...success
```

## Copy virtual machine to a different datacenter (must specify new datastore and host)
```
./vm-cp mike@vc.example.com 'Alpha Datacenter/base/linux/arch' 'Bravo Datacenter/arch-test2' --to-datastore ds-bravo-san1-vms1 --to-host vs2.brave.example.com
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Cloning "/Alpha Datacenter/base/linux/arch" to "/Alpha Datacenter/arch-test2"...success
```

## Remove virtual machine
```
./vm-rm mike@vc.example.com 'Alpha Datacenter/base/linux/arch-test2'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Removing "/Alpha Datacenter/base/linux/arch"...success
```

## Remove folder
```
./vm-rm -r mike@vc.example.com 'Alpha Datacenter/base/windows'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Removing "/Alpha Datacenter/base/windows"...success
```

## Create folder
```
./vm-mkdir mike@vc.example.com 'Alpha Datacenter/experiments'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Making "/Alpha Datacenter/experiments/"...success
```

## Create folder and intermediate folders
```
./vm-mkdir -P mike@vc.example.com 'Alpha Datacenter/experiments/new_folder_parent/new_folder_child'
Attempting to connect as "mike" to "vc.example.com"...
	Connected

Making "/Alpha Datacenter/experiments/new_folder_parent"...success
Making "/Alpha Datacenter/experiments/new_folder_parent/new_folder_child"...success
```
