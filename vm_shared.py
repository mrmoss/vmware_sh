#!/usr/bin/env python3
#  Dependencies:  pip install pyvim pyvmomi

import argparse
import csv
import getpass
import pyVim.connect
import pyVmomi
import socket
import ssl
import sys
import threading
import time

def normalize_path_str(path):
	return'/'+path.strip().strip('/')

def parse_login_line(line):
	parts=''.join(line.split()).split('@')
	if len(parts)!=2:
		raise Exception('Invalid server string "'+line+'" (expecting user@server)')
	return {'user':parts[0],'server':parts[1]}

def parse_password_csv_file(filename):
	csv_file=None
	try:
		csv_file=csv.reader(open(filename))
	except Exception:
		raise Exception('Error reading "'+filename+'"')
	rows=[]
	for row in csv_file:
		if len(row)!=2:
			raise Exception('Invalid entry on line '+str(count)+' - got '+str(len(row))+' columns (expected 2: username,password)')
		rows.append(row)
	return rows

def verbose_login(args,password=None):
	server_obj=None
	login=parse_login_line(args.login)
	sys.stderr.write('Attempting to connect as "'+login['user']+'" to "'+login['server']+'"...\n')

	password_stdin=hasattr(args,'password_stdin') and args.password_stdin
	password_file=hasattr(args,'password_file') and args.password_file

	#Passed password as arg
	if password:
		server_obj=connect_server(login['server'],login['user'],password)

	#Get password from stdin
	elif password_stdin:
		password=input()
		try:
			server_obj=connect_server(login['server'],login['user'],password)
		except Exception as error:
			sys.stderr.write('\t\tError: '+str(error)+'\n')

	#Get password from password csv file
	elif password_file:
		sys.stderr.write('\tLooking for passwords in "'+args.password_file+'"...\n')
		for row in parse_password_csv_file(args.password_file):
			if row[0]==login['user']+'@'+login['server']:
				password=row[1]
				try:
					server_obj=connect_server(login['server'],login['user'],password)
					break
				except Exception as error:
					sys.stderr.write('\t\tError: '+str(error)+'\n')
		if not server_obj:
			sys.stderr.write('\tNo valid password found in password file\n')

	#Above failed, prompt for password
	if not server_obj and not password_stdin and not password_file:
		password=getpass.getpass(prompt='\tPassword: ')
		server_obj=connect_server(login['server'],login['user'],password)

	sys.stderr.write('\tConnected\n\n')
	return server_obj

def connect_server(server,user,password):
	try:
		si=pyVim.connect.SmartConnect(host=server,user=user,pwd=password,sslContext=ssl.create_default_context())
		content=si.RetrieveContent()
		return {'si':si,'content':content}

	except pyVmomi.vim.fault.InvalidLogin:
		raise Exception('Login error')

	except socket.error:
		raise Exception('Could not connect to "'+server_str[1]+'"')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def disconnect_server(server_obj):
	if server_obj and 'si' in server_obj and server_obj['si']:
		pyVim.connect.Disconnect(server_obj['si'])

def get_path_parent(path):
	return normalize_path_str('/'.join(path.split('/')[:-1]))

def get_path_top(path):
	return path.split('/')[-1]

def object_is_datacenter(obj):
	return isinstance(obj,pyVmomi.vim.Datacenter)

def object_is_folder(obj):
	return isinstance(obj,pyVmomi.vim.Folder)

def object_is_vm(obj):
	return isinstance(obj,pyVmomi.vim.VirtualMachine)

def get_datacenter_objects(server_obj):
	datacenters=[]
	for datacenter in [entity for entity in server_obj['content'].rootFolder.childEntity if hasattr(entity,'vmFolder')]:
		datacenters.append(datacenter)
	return datacenters

def list_datacenters(server_obj):
	names=[]
	for datacenter in get_datacenter_objects(server_obj):
		names.append(datacenter.name)
	names.sort()
	return names

def datacenter_from_str(server_obj,datacenter_str):
	for datacenter in get_datacenter_objects(server_obj):
		if datacenter.name==datacenter_str:
			return datacenter
	raise Exception('Could not find datacenter "'+datacenter_str+'"')

def get_cluster_objects(server_obj,datacenter_obj):
	clusters=[]
	for cluster in datacenter_obj.hostFolder.childEntity:
		clusters.append(cluster)
	return clusters

def list_clusters(server_obj,datacenter_str):
	names=[]
	for cluster in get_cluster_objects(server_obj,datacenter_from_str(server_obj,datacenter_str)):
		names.append(cluster.name)
	names.sort()
	return names

def cluster_from_str(server_obj,datacenter_str,cluster_str):
	for cluster in get_cluster_objects(server_obj,datacenter_from_str(server_obj,datacenter_str)):
		if cluster.name==cluster_str:
			return cluster
	raise Exception('Could not find cluster "'+cluster_str+'" in datacenter "'+datacenter_str+'"')

def get_datastore_objects(server_obj,datacenter_obj):
	datastores=[]
	for datastore in datacenter_obj.datastore:
		datastores.append(datastore)
	return datastores

def list_datastores(server_obj,datacenter_str):
	names=[]
	for datastore in get_datastore_objects(server_obj,datacenter_from_str(server_obj,datacenter_str)):
		names.append(datastore.name)
	names.sort()
	return names

def datastore_from_str_without_datacenter(server_obj,datastore_str):
	for datacenter in get_datacenter_objects(server_obj):
		for datastore in get_datastore_objects(server_obj,datacenter):
			if datastore.name==datastore_str:
				return datastore
	raise Exception('Could not find datastore "'+datastore_str+'" in any datacenter')

def get_host_objects(server_obj,cluster_obj):
	hosts=[]
	for host in cluster_obj.host:
		hosts.append(host)
	return hosts

def get_all_host_objects(server_obj):
	hosts=[]
	for datacenter in get_datacenter_objects(server_obj):
		for cluster in get_cluster_objects(server_obj,datacenter):
			for host in get_host_objects(server_obj,cluster):
				hosts.append(host)
	return hosts

def list_hosts(server_obj,datacenter_str,cluster_str):
	names=[]
	for host in get_host_objects(server_obj,cluster_from_str(server_obj,datacenter_str,cluster_str)):
		names.append(host.name)
	names.sort()
	return names

def host_from_str(server_obj,datacenter_str,cluster_str,host_str):
	for host in get_host_objects(server_obj,cluster_from_str(server_obj,datacenter_str,cluster_str)):
		if host.name==host_str:
			return host
	raise Exception('Could not find host "'+host_str+'" in cluster "'+cluster_str+'" in datacenter "'+datacenter_str+'"')

def host_from_str_without_datacenter(server_obj,host_str):
	for datacenter in get_datacenter_objects(server_obj):
		for cluster in get_cluster_objects(server_obj,datacenter):
			for host in get_host_objects(server_obj,cluster):
				if host.name==host_str:
					return host
	raise Exception('Could not find host "'+host_str+'" in any datacenter')

def host_from_str_without_cluster(server_obj,datacenter_str,host_str):
	for cluster in datacenter_from_str(server_obj,datacenter_str).hostFolder.childEntity:
		for host in get_host_objects(server_obj,cluster):
			if host.name==host_str:
				return host
	raise Exception('Could not find host "'+host_str+'" in any cluster in datacenter "'+datacenter_str+'"')

def get_network_objects(server_obj,host_obj):
	networks=[]
	for network in host_obj.network:
		networks.append(network)
	return networks

def list_networks(server_obj,datacenter_str,cluster_str,host_str):
	names=[]
	for network in get_network_objects(server_obj,host_from_str(server_obj,datacenter_str,cluster_str,host_str)):
		names.append(network.name)
	names.sort()
	return names

def network_from_str(server_obj,datacenter_str,cluster_str,host_str,network_str):
	for network in get_network_objects(server_obj,host_from_str(server_obj,datacenter_str,cluster_str,host_str)):
		if network.name==network_str:
			return network
	raise Exception('Could not find network "'+network_str+'" in host "'+host_str+'" in cluster "'+cluster_str+'" in datacenter "'+datacenter_str+'"')

def object_from_str(server_obj,path):
	paths=path.strip('/').split('/')
	if len(paths)<=0:
		return None
	for child in server_obj['content'].rootFolder.childEntity:
		if child.name==paths[0]:
			return object_from_str_parent_m(child,paths[1:])
	return None

def vm_from_str(server_obj,vm_str):
	obj=object_from_str(server_obj,vm_str)
	if object_is_vm(obj):
		return obj
	if obj==None:
		raise Exception('"'+vm_str+'" does not exist.')
	else:
		raise Exception('"'+vm_str+'" is not a VM.')

def poweroff_vm_obj(server_obj,vm_obj):
	try:
		if vm_obj.summary.runtime.powerState!='poweredOff':
			wait_for_tasks_m(server_obj['si'],[vm_obj.PowerOff()])

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except (pyVmomi.vim.fault.InvalidPowerState,pyVmomi.vim.fault.InvalidState):
		raise Exception('VM is in an invalid state.')

	except pyVmomi.vmodl.fault.NotSupported:
		raise Exception('VM is a template.')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def poweron_vm_obj(server_obj,vm_obj):
	try:
		if vm_obj.summary.runtime.powerState!='poweredOn':
			wait_for_tasks_m(server_obj['si'],[vm_obj.PowerOn()])

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except (pyVmomi.vim.fault.InvalidPowerState,pyVmomi.vim.fault.InvalidState):
		raise Exception('VM is in an invalid state.')

	except pyVmomi.vmodl.fault.NotSupported:
		raise Exception('VM is a template.')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def list_structures(server_obj,path_str,full_paths=False,folders_only=False,machines_only=False):
	obj=object_from_str(server_obj,path_str)
	structures=[]

	if object_is_vm(obj) and not folders_only:
		structures.append(list_structures_helper_m(path_str,obj.name,full_paths))
		return structures

	if object_is_folder(obj) or object_is_datacenter(obj):
		children=None
		if object_is_folder(obj):
			children=obj.childEntity
		else:
			children=obj.vmFolder.childEntity

		for child in children:
			if object_is_vm(child) and not folders_only:
				structures.append(list_structures_helper_m(path_str,child.name,full_paths))
			elif object_is_folder(child) and not machines_only:
				structures.append(list_structures_helper_m(path_str,child.name,full_paths))
		return structures

	if obj==None:
		raise Exception('"'+path_str+'" does not exist.')
	else:
		raise Exception('"'+path_str+'" is not a traversable.')

def mv_obj(server_obj,src_obj,datacenter_or_folder_obj):
	try:
		if object_is_datacenter(datacenter_or_folder_obj):
			datacenter_or_folder_obj=datacenter_or_folder_obj.vmFolder

		wait_for_tasks_m(server_obj['si'],[datacenter_or_folder_obj.MoveInto([src_obj])])

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except pyVmomi.vim.fault.InvalidState:
		raise Exception('VM is in an invalid state.')

	except pyVmomi.vmodl.fault.NotSupported:
		raise Exception('Datacenter change - Not supported...vm-cp and then vm-rm original to move.')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def rename_obj(server_obj,obj,new_name):
	try:
		wait_for_tasks_m(server_obj['si'],[obj.Rename(new_name)])

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except pyVmomi.vim.fault.InvalidState:
		raise Exception('VM is in an invalid state.')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def vm_snapshot(server_obj,vm_obj,snapshot_name):
	try:
		wait_for_tasks_m(server_obj['si'],[vm_obj.CreateSnapshot(snapshot_name,'',False,False)])

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except pyVmomi.vim.fault.InvalidState:
		raise Exception('VM is in an invalid state.')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def get_snapshot_objects(vm_obj):
	snapshots=[]
	if not vm_obj.snapshot==None:
		for snapshot in vm_obj.snapshot.rootSnapshotList:
			snapshots.append(('/'+snapshot.name,snapshot.snapshot))
			get_snapshot_objects_recursive_m(snapshots,'/'+snapshot.name,snapshot)
	return snapshots

def vm_snapshot_list(vm_obj):
	snapshots=[]
	for snapshot in get_snapshot_objects(vm_obj):
		snapshots.append(snapshot[0])
	return snapshots

def vm_snapshot_remove(server_obj,snapshot_obj):
	try:
		wait_for_tasks_m(server_obj['si'],[snapshot_obj.RemoveSnapshot_Task(True)])

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except pyVmomi.vim.fault.InvalidState:
		raise Exception('VM is in an invalid state.')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def vm_snapshot_revert(server_obj,snapshot_obj):
	try:
		wait_for_tasks_m(server_obj['si'],[snapshot_obj.RevertToSnapshot_Task()])

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except pyVmomi.vim.fault.InvalidState:
		raise Exception('VM is in an invalid state.')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def vm_copy_nowait(server_obj,from_vm_obj,to_folder_obj,to_name,from_snapshot_obj=None,to_host_obj=None,to_datastore_obj=None):
	relospec=pyVmomi.vim.vm.RelocateSpec()

	if not to_host_obj:
		to_host_obj=from_vm_obj.runtime.host

	relospec.host=to_host_obj
	relospec.pool=to_host_obj.parent.resourcePool

	same_datastore=False
	if to_datastore_obj:
		for datastore in from_vm_obj.datastore:
			if datastore.name==to_datastore_obj.name:
				same_datastore=True
				break

	if from_snapshot_obj and (same_datastore or not to_datastore_obj):
		relospec.diskMoveType='createNewChildDiskBacking'

	if to_datastore_obj:
		relospec.datastore=to_datastore_obj

	try:
		clone_spec=pyVmomi.vim.vm.CloneSpec(location=relospec,template=False,powerOn=False,snapshot=from_snapshot_obj,memory=False)
		return from_vm_obj.Clone(folder=to_folder_obj,name=to_name,spec=clone_spec)

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except pyVmomi.vim.fault.InvalidState:
		raise Exception('VM is in an invalid state.')

	except pyVmomi.vmodl.fault.InvalidArgument as error:
		if isinstance(error.faultCause,pyVmomi.vim.fault.DatacenterMismatch):
			raise Exception('Datacenter change - must specify new datastore and host.')
		raise

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def vm_copy(server_obj,from_vm_obj,to_folder_obj,to_name,from_snapshot_obj=None,to_host_obj=None,to_datastore_obj=None):
	try:
		wait_for_tasks_m(server_obj['si'],[vm_copy_nowait(server_obj,from_vm_obj,to_folder_obj,to_name,from_snapshot_obj,to_host_obj,to_datastore_obj)])

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except pyVmomi.vim.fault.InvalidState:
		raise Exception('VM is in an invalid state.')

	except pyVmomi.vmodl.fault.InvalidArgument as error:
		if isinstance(error.faultCause,pyVmomi.vim.fault.DatacenterMismatch):
			raise Exception('Datacenter change - must specify new datastore and host.')
		raise

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def object_remove(server_obj,path_obj):

	#Datacenter - stop
	if object_is_datacenter(path_obj):
		raise Exception('Cannot remove datacenter.')

	#Remove
	try:
		wait_for_tasks_m(server_obj['si'],[path_obj.Destroy_Task()])

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except pyVmomi.vim.fault.InvalidState:
		raise Exception('VM is in an invalid state.')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def mk_folder(server_obj,parent_obj,new_folder_name,full_path):
	try:
		if object_is_datacenter(parent_obj):
			parent_obj=parent_obj.vmFolder
		parent_obj.CreateFolder(new_folder_name)
		full_path=normalize_path_str(full_path)

		#Wait for folder creation (seems more reliable than the wait_for_tasks in this specific instance)...
		while True:
			time.sleep(0.1)
			if object_from_str(server_obj,full_path):
				break

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def role_id_from_str(server_obj,role_str):
	for role in server_obj['content'].authorizationManager.roleList:
		if role.name==role_str:
			return role.roleId
	raise Exception('Could not find the role "'+role_str+'"')

def role_str_from_id(server_obj,role_id):
	for role in server_obj['content'].authorizationManager.roleList:
		if role.roleId==role_id:
			return role.name
	raise Exception('Could not find the role id "'+str(role_id)+'"')

def normalize_user_str(user_str):
	return user_str.replace('/','\\').strip('\\')

def user_object_to_str(user_obj):
	return user_obj['domain']+'\\'+user_obj['user']

def user_from_str(server_obj,user_str):

	#Parse domain and user
	user_parts=normalize_user_str(user_str).split('\\')
	if len(user_parts)!=2:
		raise Exception('Invalid username "'+user_str+'" (format is DOMAIN/USERNAME)')
	domain=user_parts[0]
	user=user_parts[1]

	#Validate domain
	if domain not in server_obj['content'].userDirectory.domainList:
		raise Exception('Domain "'+user+'" was not found.')

	#Validate user
	found_user=False
	for query in server_obj['content'].userDirectory.RetrieveUserGroups(domain=domain,searchStr='',exactMatch=False,findUsers=True,findGroups=False):
		if query.principal==user:
			found_user=True
			break
	if not found_user:
		raise Exception('User "'+user+'" was not found in the domain "'+domain+'".')

	#Return validated user
	return {'user':user,'domain':domain}

def add_user_perm(server_obj,role_id,user_obj,obj):
	try:
		perm=pyVmomi.vim.AuthorizationManager.Permission(principal=user_object_to_str(user_obj),group=False,roleId=role_id,propagate=True)
		server_obj['content'].authorizationManager.SetEntityPermissions(obj,[perm])

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def del_user_perm(server_obj,role_id,user_obj,obj,force=False):
	#Convert user object into user string
	user_str=None
	if user_obj:
		user_str=user_object_to_str(user_obj)

	#Get permissions and filter out the unwanted permission
	current_perms=list_user_perms(server_obj,obj)
	new_perms=[]

	for perm in current_perms:

		remove=True

		if role_id!=None and perm.roleId!=role_id:
			remove=False

		if user_str!=None and perm.principal!=user_str:
			remove=False

		if not remove:
			new_perms.append(perm)

	#Permission was not remove - stop if no force
	if len(current_perms)==len(new_perms):
		if force:
			return
		raise Exception('Permission not found on object.')

	#Set filtered permissions
	try:
		server_obj['content'].authorizationManager.ResetEntityPermissions(obj,new_perms)

	except pyVmomi.vim.fault.NotFound:
		raise Exception('Permission not found on object.')

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def list_user_perms(server_obj,obj):
	try:
		return server_obj['content'].authorizationManager.RetrieveEntityPermissions(obj,inherited=False)

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def get_interface_objects(vm_obj):
	nics=[]
	for device in vm_obj.config.hardware.device:
		if isinstance(device,pyVmomi.vim.vm.device.VirtualEthernetCard):
			nics.append(device)
	return nics

def get_interface_network_name(server_obj,raw_nic_obj):
	#Get standard name
	network=raw_nic_obj.deviceInfo.summary

	#Get switch network if connected to a switch
	try:
		uuid=raw_nic_obj.backing.port.switchUuid
		port_group_key=raw_nic_obj.backing.port.portgroupKey
		network=server_obj['content'].dvSwitchManager.QueryDvsByUuid(uuid).LookupDvPortGroup(port_group_key).summary.name

	#Fails if it's not a dvswitch...
	except Exception:
		pass

	#All done
	return network

def get_interface_info(server_obj,vm_obj):
	#Get most of the nic info
	nics={}
	for nic in get_interface_objects(vm_obj):

		#Get basics
		nic_obj=generate_new_nic_obj_m()
		nic_obj['name']=nic.deviceInfo.label
		nic_obj['network']=get_interface_network_name(server_obj,nic)
		nic_obj['host']=vm_obj.runtime.host.name
		nic_obj['mac']=nic.macAddress
		nic_obj['connect_on_boot']=nic.connectable.startConnected
		nic_obj['connected']=nic.connectable.connected
		nic_obj['allow_guest_control']=nic.connectable.allowGuestControl
		nic_obj['obj']=nic

		#Store in dict
		key=nic_obj['name']+nic_obj['network']+nic_obj['mac']
		nics[key]=nic_obj

	#Get IP addresses (why aren't these in the above object???)
	for nic in vm_obj.guest.net:
		for key in nics:

			#Find the network
			if nics[key]['network']==nic.network and nics[key]['mac']==nic.macAddress:

				#Store IPs
				for address in nic.ipConfig.ipAddress:
					format_str='%s/%d'
					if address.ipAddress.find(':')>=0:
						format_str='[%s]/%d'
					nics[key]['addresses'].append(format_str%(address.ipAddress,address.prefixLength))

				#Sort IPs
				nics[key]['addresses'].sort()
				break

	return nics

def change_interface_network(server_obj,vm_obj,nic_obj,new_network_obj):
	try:
		nicspec=pyVmomi.vim.vm.device.VirtualDeviceSpec()
		nicspec.operation=pyVmomi.vim.vm.device.VirtualDeviceSpec.Operation.edit
		nicspec.device=nic_obj['obj']
		nicspec.device.wakeOnLanEnabled=True

		if isinstance(new_network_obj,pyVmomi.vim.dvs.DistributedVirtualPortgroup):
			port_obj=pyVmomi.vim.dvs.PortConnection()
			port_obj.portgroupKey=new_network_obj.key
			port_obj.switchUuid=new_network_obj.config.distributedVirtualSwitch.uuid
			nicspec.device.backing=pyVmomi.vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
			nicspec.device.backing.port=port_obj
		else:
			nicspec.device.backing=pyVmomi.vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
			nicspec.device.backing.network=new_network_obj
			nicspec.device.backing.deviceName=new_network_obj.name

		nicspec.device.connectable=pyVmomi.vim.vm.device.VirtualDevice.ConnectInfo()
		nicspec.device.connectable.connected=nic_obj['connect_on_boot']
		nicspec.device.connectable.startConnected=nic_obj['connect_on_boot']
		nicspec.device.connectable.allowGuestControl=nic_obj['allow_guest_control']

		config_spec=pyVmomi.vim.vm.ConfigSpec(deviceChange=[nicspec])
		wait_for_tasks_m(server_obj['si'],[vm_obj.ReconfigVM_Task(config_spec)])

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))

def mk_vswitch(host_obj,vswitch_name,port_count=56):
	vss_spec=pyVmomi.vim.host.VirtualSwitch.Specification()
	vss_spec.numPorts=port_count
	host_obj.configManager.networkSystem.AddVirtualSwitch(vswitchName=vswitch_name,spec=vss_spec)

def del_vswitch(host_obj,vswitch_name):
	host_obj.configManager.networkSystem.RemoveVirtualSwitch(vswitch_name)

def mk_portgroup(host_obj,vswitch_name,portgroup_name,vlan_id,allow_promiscuous=False,allow_forged_transmits=True,allow_mac_changes=True):
	portgroup_spec=pyVmomi.vim.host.PortGroup.Specification()
	portgroup_spec.vswitchName=vswitch_name
	portgroup_spec.name=portgroup_name
	portgroup_spec.vlanId=vlan_id

	secpol=pyVmomi.vim.host.NetworkPolicy.SecurityPolicy()
	secpol.allowPromiscuous=allow_promiscuous
	secpol.forgedTransmits=allow_forged_transmits
	secpol.macChanges=allow_mac_changes
	portgroup_spec.policy=pyVmomi.vim.host.NetworkPolicy(security=secpol)

	host_obj.configManager.networkSystem.AddPortGroup(portgrp=portgroup_spec)

#Internal helpers...don't use?
wait_lock=threading.Lock()

def object_from_str_parent_m(parent,paths):
	if len(paths)<=0:
		return parent
	if hasattr(parent,'vmFolder'):
		for child in parent.vmFolder.childEntity:
			if child.name==paths[0]:
				return object_from_str_child_m(child,paths[1:])
	return None

def object_from_str_child_m(parent,paths):
	if len(paths)<=0:
		return parent
	if hasattr(parent,'childEntity'):
		for child in parent.childEntity:
			if child.name==paths[0]:
				return object_from_str_child_m(child,paths[1:])
	return None

def list_structures_helper_m(parent_path,obj_path,full_paths):
	if not full_paths:
		return obj_path
	return normalize_path_str(parent_path)+'/'+obj_path

def wait_for_tasks_m(service_instance,tasks):
	while True:
		try:
			done=True
			for task in tasks:
				info=task.info
				if info.state==pyVmomi.vim.TaskInfo.State.running or info.state==pyVmomi.vim.TaskInfo.State.queued:
					done=False
					break
			if done:
				break
		except Exception:
			pass
		time.sleep(0.1)

def get_snapshot_objects_recursive_m(snapshots,snapshot_path,snapshot_obj):
	if len(snapshot_obj.childSnapshotList)>0:
		for snapshot in snapshot_obj.childSnapshotList:
			new_path=snapshot_path+'/'+snapshot.name
			snapshots.append((new_path,snapshot.snapshot))
			get_snapshot_objects_recursive_m(snapshots,new_path,snapshot)
	return snapshots

def generate_new_nic_obj_m():
	return {'name':'Unknown','network':'Unknown','host':'Unknown','mac':'Unknown','connect_on_boot':False,
		'connected':False,'obj':None,'addresses':[],'allow_guest_control':False}