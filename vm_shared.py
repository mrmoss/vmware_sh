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

def verbose_login(args):
	server_obj=None
	login=parse_login_line(args.login)
	sys.stderr.write('Attempting to connect as "'+login['user']+'" to "'+login['server']+'"...\n')

	if args.password_file:
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
	if not args.password_file or not server_obj:
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

def obj_is_datacenter(obj):
	return isinstance(obj,pyVmomi.vim.Datacenter)

def obj_is_folder(obj):
	return isinstance(obj,pyVmomi.vim.Folder)

def obj_is_vm(obj):
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
	if obj_is_vm(obj):
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

	if obj_is_vm(obj) and not folders_only:
		structures.append(list_structures_helper_m(path_str,obj.name,full_paths))
		return structures

	if obj_is_folder(obj) or obj_is_datacenter(obj):
		children=None
		if obj_is_folder(obj):
			children=obj.childEntity
		else:
			children=obj.vmFolder.childEntity

		for child in children:
			if obj_is_vm(child) and not folders_only:
				structures.append(list_structures_helper_m(path_str,child.name,full_paths))
			elif obj_is_folder(child) and not machines_only:
				structures.append(list_structures_helper_m(path_str,child.name,full_paths))
		return structures

	if obj==None:
		raise Exception('"'+path_str+'" does not exist.')
	else:
		raise Exception('"'+path_str+'" is not a traversable.')

def mv_obj(server_obj,src_obj,datacenter_or_folder_obj):
	try:
		if obj_is_datacenter(datacenter_or_folder_obj):
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

def vm_copy(server_obj,from_vm_obj,to_folder_obj,to_name,from_snapshot_obj=None,to_host_obj=None,to_datastore_obj=None):
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
		wait_for_tasks_m(server_obj['si'],[from_vm_obj.Clone(folder=to_folder_obj,name=to_name,spec=clone_spec)])

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

def obj_remove(server_obj,path_obj):

	#Datacenter - stop
	if obj_is_datacenter(path_obj):
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
		if obj_is_datacenter(parent_obj):
			parent_obj=parent_obj.vmFolder

		parent_obj.CreateFolder(new_folder_name)
		full_path=normalize_path_str(full_path)

		#Wait for folder creation (seems more reliable than the wait_for_tasks in this specific instance...
		while True:
			time.sleep(0.1)
			if object_from_str(server_obj,full_path):
				break

	except pyVmomi.vim.fault.NoPermission:
		raise Exception('Insufficient permissions')

	except Exception as error:
		raise Exception('Unexpected error - '+str(error))










#Internal helpers...don't use?
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

def wait_for_tasks_m(service_instance, tasks):
	property_collector = service_instance.content.propertyCollector
	task_list = [str(task) for task in tasks]
	# Create filter
	obj_specs = [pyVmomi.vmodl.query.PropertyCollector.ObjectSpec(obj=task)
				 for task in tasks]
	property_spec = pyVmomi.vmodl.query.PropertyCollector.PropertySpec(type=pyVmomi.vim.Task,
															   pathSet=[],
															   all=True)
	filter_spec = pyVmomi.vmodl.query.PropertyCollector.FilterSpec()
	filter_spec.objectSet = obj_specs
	filter_spec.propSet = [property_spec]
	pcfilter = property_collector.CreateFilter(filter_spec, True)
	try:
		version, state = None, None
		# Loop looking for updates till the state moves to a completed state.
		while len(task_list):
			update = property_collector.WaitForUpdates(version)
			for filter_set in update.filterSet:
				for obj_set in filter_set.objectSet:
					task = obj_set.obj
					for change in obj_set.changeSet:
						if change.name == 'info':
							state = change.val.state
						elif change.name == 'info.state':
							state = change.val
						else:
							continue

						if not str(task) in task_list:
							continue

						if state == pyVmomi.vim.TaskInfo.State.success:
							# Remove task from taskList
							task_list.remove(str(task))
						elif state == pyVmomi.vim.TaskInfo.State.error:
							raise task.info.error
			# Move to next version
			version = update.version
	finally:
		if pcfilter:
			pcfilter.Destroy()

def get_snapshot_objects_recursive_m(snapshots,snapshot_path,snapshot_obj):
	if len(snapshot_obj.childSnapshotList)>0:
		for snapshot in snapshot_obj.childSnapshotList:
			new_path=snapshot_path+'/'+snapshot.name
			snapshots.append((new_path,snapshot.snapshot))
			get_snapshot_objects_recursive_m(snapshots,new_path,snapshot)
	return snapshots