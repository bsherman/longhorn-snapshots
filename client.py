#!/usr/bin/env python3

import longhorn
import json
import os
import sys
from operator import itemgetter

SAFE_SNAPSHOTS=29

if 2 > len(sys.argv):
  print("USAGE: main.py PVC_NAME [NAMESPACE]")
  print("               PVC_NAME - pvc volume on which to operate")
  print("               NAMESPACE - defaults to 'default'")
  sys.exit(1)

pvc_name = sys.argv[1]

if 3 <= len(sys.argv):
  pvc_ns = sys.argv[2]

# If automation/scripting tool is inside the same cluster in which Longhorn is installed
#  example:  https://my-longhorn.url/v1
longhorn_url = os.environ['LONGHORN_URL']

client = longhorn.Client(url=longhorn_url)

# Volume operations
# List all volumes
#volumes = client.list_volume()
# Get volume by NAME/ID
#testvol1 = client.by_id_volume(id="testvol1")
# Attach TESTVOL1
#testvol1 = testvol1.attach(hostId="worker-1")
# Detach TESTVOL1
#testvol1.detach()
# Create a snapshot of TESTVOL1 with NAME
#snapshot1 = testvol1.snapshotCreate(name="snapshot1")
# Create a backup from a snapshot NAME
#testvol1.snapshotBackup(name=snapshot1.name)
# Update the number of replicas of TESTVOL1
#testvol1.updateReplicaCount(replicaCount=2)
# Find more examples in Longhorn integration tests https://github.com/longhorn/longhorn-tests/tree/master/manager/integration/tests

# Node operations
# List all nodes
#nodes = client.list_node()
# Get node by NAME/ID
#node1 = client.by_id_node(id="worker-1")
# Disable scheduling for NODE1
#client.update(node1, allowScheduling=False)
# Enable scheduling for NODE1
#client.update(node1, allowScheduling=True)
# Find more examples in Longhorn integration tests https://github.com/longhorn/longhorn-tests/tree/master/manager/integration/tests

# Setting operations
# List all settings
#settings = client.list_setting()


volumes = client.list_volume()
i = 0
for v in volumes.data:
  if i == 0:
    #print(v.keys())
    i = i+1


  if pvc_name == v.kubernetesStatus['pvcName']:
    #print(f"{v.name}, {v.kubernetesStatus['namespace']}, {v.kubernetesStatus['pvcName']}")
    snapshots = v.snapshotList()
    
    ordered = sorted(snapshots.data, key = itemgetter("created"))
    c = 0
    d = 0
    for s in ordered:
      c += 1
      # do not operate on the last {SAFE_SNAPSHOTS} snapshots
      if c+SAFE_SNAPSHOTS <= len(snapshots):
        d += 1
        print(f"deleting old snapshot: {s.name} ({s.created}) {round(int(s.size)/1024/1024,1)} MB - children {s.children}")
        if not s.removed:
          v.snapshotDelete(name=s.name)
      
    print(f"snapshots total: {len(snapshots)}")
    print(f"evaluated: {c}")
    
    if 0 < d:
      v.snapshotPurge()   
      print(f"deleted: {d}")

    #print(snapshots.data)
        