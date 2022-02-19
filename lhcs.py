#!/usr/bin/env python3

import longhorn

import argparse
import json
import os

from operator import itemgetter


parser = argparse.ArgumentParser(description="A client to list information about Longhorn PVCs and their snapshots, and remove snapshots when desired.\n--list or --remove must be used to choose a primary action.",
                                 epilog="--url is required if 'LONGHORN_URL' is not specified in the environment.\n\n\nNOTE: it takes Longhorn some time to process deletions, please be patient and monitor via the dashboard.")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-L", "--list", action='store_true',
                   help="list PVC information")
group.add_argument("-R", "--remove", action='store_true',
                   help="remove PVC snapshots")

parser.add_argument("-N", "--namespace", help="limit to specified namespace")
parser.add_argument(
    "-P", "--pvc", help="limit to specified name (multiple PVCs can have the same name if in different namespaces)")
parser.add_argument("-S", "--snap-pattern",
                    help="limit to snapshot names matching this pattern")

parser.add_argument("-n", "--dry-run", action='store_true',
                    help="a dry-run will make no changes to the PVCs or snapshots")
parser.add_argument("-c", "--retain-count", type=int, default=30,
                    help="number of snapshots to retain (default: 30)")
parser.add_argument("-v", "--verbose", action='store_true',
                    help="show snapshot detail when listing and verbose info when removing")

require_url = None is os.environ.get('LONGHORN_URL', None)
parser.add_argument("-u", "--url", default=os.environ.get('LONGHORN_URL'),
                    help="longhorn API URL (default: environment value of 'LONGHORN_URL')", required=require_url)

args = parser.parse_args()


client = longhorn.Client(url=args.url)

# get the volumes and separate by namespaces and pvcname
volumes_full = client.list_volume()
volumes_ns_pvc = dict()
for v in volumes_full.data:
    if 'detached' == v.state:
        print(f"skipping {v.name}({v.kubernetesStatus['pvcName']}): snapshot operations unavailable for detached volume")
        continue

    if v.kubernetesStatus['namespace'] not in volumes_ns_pvc.keys():
        volumes_ns_pvc[v.kubernetesStatus['namespace']] = dict()

    volumes_ns_pvc[v.kubernetesStatus['namespace']
                   ][v.kubernetesStatus['pvcName']] = v
    snapshots_full = v.snapshotList()
    snapshots_size = 0
    snapshot_head = None
    my_snapshots = list()

    for s in snapshots_full.data:
        if 'volume-head' == s.name or (args.snap_pattern is not None and args.snap_pattern not in s.name):
            continue

        my_snapshots.append(s)
        snapshots_size += int(s.size)

    snapshots_sorted = sorted(my_snapshots, key=itemgetter("created"))
    v.snapshots_sorted = snapshots_sorted
    v.snapshots_size = snapshots_size


if args.list:
    # exec list mode
    total_snapshots = 0
    total_size = 0
    print(f"NAMESPACE\tPVC_NAME\tPV_NAME\tSNAPSHOT_COUNT\tSNAPSHOT_SIZE")
    for ns in sorted(volumes_ns_pvc.keys()):
        if args.namespace != ns and args.namespace is not None:
            continue

        for pvc in sorted(volumes_ns_pvc[ns].keys()):
            if args.pvc != pvc and args.pvc is not None:
                continue

            v = volumes_ns_pvc[ns][pvc]
            total_snapshots += len(v.snapshots_sorted)
            total_size += int(v.snapshots_size)
            print(
                f"{ns}\t{pvc}\t{v.name}\t{len(v.snapshots_sorted)}\t{round(int(v.snapshots_size)/1024/1024,1)} MB")
            if args.verbose:
                for s in v.snapshots_sorted:
                    deleting = "removal in progress" if s.removed else ""
                    print(
                        f"|- {s.name}\t{s.created}\t{round(int(s.size)/1024/1024,1)} MB\tchildren {s.children}\t{deleting}")

    if None is args.pvc:
        print(
            f"\nTOTAL\tALL\tVOLSNAPSHOTS\t{total_snapshots}\t{round(total_size/1024/1024,1)} MB")

elif args.remove:
    # exec remove mode
    txt_delete = "would delete" if args.dry_run else "deleting"
    txt_deleted = "would have deleted" if args.dry_run else "deleted"
    txt_submit = "would submit" if args.dry_run else "submitted"

    total_deleted_snapshots = 0
    total_deleted_size = 0
    for ns in sorted(volumes_ns_pvc.keys()):
        if args.namespace != ns and args.namespace is not None:
            continue

        for pvc in sorted(volumes_ns_pvc[ns].keys()):
            if args.pvc != pvc and args.pvc is not None:
                continue

            deleted_snapshots = 0
            deleted_size = 0
            v = volumes_ns_pvc[ns][pvc]
            c = len(v.snapshots_sorted)  # count of retained snaps
            print(f"{ns}/{pvc}: {c} snapshots")
            for s in v.snapshots_sorted:
                if c <= args.retain_count:
                    break

                c -= 1
                deleted_snapshots += 1
                total_deleted_snapshots += 1
                deleted_size += int(s.size)
                total_deleted_size += int(s.size)

                if args.verbose:
                    print(
                        f"{txt_delete} {ns}/{pvc}/{s.name}\t{s.created}\t{round(int(s.size)/1024/1024,1)} MB")
                if not args.dry_run:
                    # if not s.removed:
                    v.snapshotDelete(name=s.name)

            if 0 < deleted_snapshots:
                print(
                    f"{ns}/{pvc}: {txt_deleted} {deleted_snapshots} snapshots, combined size {round(deleted_size/1024/1024,1)} MB")
                if args.verbose:
                    print(f"{txt_submit} purge request for {ns}/{pvc}")
                if not args.dry_run:
                    v.snapshotPurge()

    if None is args.pvc:
        print(
            f"\nTOTAL: {txt_deleted} {total_deleted_snapshots} snapshots, combined size {round(total_deleted_size/1024/1024,1)} MB")

    if 0 < total_deleted_snapshots:
        print(f"\nNOTE: it takes Longhorn some time to process deletions, please be patient and monitor via the dashboard.")

else:
    print("Here be dragons!")
