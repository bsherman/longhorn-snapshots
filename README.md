# lhcs - Longhorn Client for Snapshots Management

[Longhorn](https://longhorn.io) is an easy-to-use distributed block storage system for Kubernetes.

It provides many features via its web UI dashboard. But sometimes it is helpful to have a bit more insight.

This tool uses the provided [Longhorn Python Client](https://longhorn.io/docs/1.2.3/references/longhorn-client-python) library to enable a user friendly CLI client for Longhorn.

This tool was inspired by this feature request to [automatically purge old unused snapshots](https://github.com/longhorn/longhorn/issues/2732). In this Github issue a [script exists](https://github.com/longhorn/longhorn/issues/2732) which is very similar to my own.

Like the linked script, this one could be used in a cronjob to clean snapshots regularly.

## Features

### List Volumes and Snapshots

Listing is accomplished using the `-L / --list` option.

Each volume is listed with:

- kubernetes namespace
- kubernetes PVC name
- kubernetes PV name
- number of Longhorn snapshots
- combined snapshot size

```bash
$ ./lhcs.py -L 
NAMESPACE       PVC_NAME        PV_NAME SNAPSHOT_COUNT  SNAPSHOT_SIZE
games   mc-creative-minecraft-bedrock   pvc-ad746514-ea7d-46a2-ab9a-6640adf3cc1f        15      1062.1 MB
games   mc-survival-minecraft-bedrock   pvc-260d3d45-faf6-40c9-9058-236da46435b0        15      724.8 MB
games   valheim-config  pvc-36aee2fa-fe18-4b6c-b007-19e3b4536d21        15      8938.7 MB
home    esphome pvc-ef709ad6-1035-4c39-8137-4459faefd87f        15      443.8 MB
home    gitea   pvc-fe8945b2-5f1d-4dac-bc7c-c781e1fa82d6        15      592.9 MB
unifi   unifi   pvc-8a450701-cdff-4c82-b406-3f8459ef106b        15      9907.4 MB

TOTAL   ALL     VOLSNAPSHOTS    90      21669.7 MB
```

This can be filtered by namespace with `-N / --namespace`:

```bash
$ ./lhcs.py -L -N home
NAMESPACE       PVC_NAME        PV_NAME SNAPSHOT_COUNT  SNAPSHOT_SIZE
home    esphome pvc-ef709ad6-1035-4c39-8137-4459faefd87f        15      443.8 MB
home    gitea   pvc-fe8945b2-5f1d-4dac-bc7c-c781e1fa82d6        15      593.1 MB

TOTAL   ALL     VOLSNAPSHOTS    30      1036.9 MB
```

or by PVC name with `-P / --pvc`:

```bash
$ ./lhcs.py -L -P unifi
NAMESPACE       PVC_NAME        PV_NAME SNAPSHOT_COUNT  SNAPSHOT_SIZE
unifi   unifi   pvc-8a450701-cdff-4c82-b406-3f8459ef106b        15      9909.4 MB
```

or both, but in this example, the combination of namespace and PVC name has no results:

```bash
$ ./lhcs.py -L -N home -P unifi 
NAMESPACE       PVC_NAME        PV_NAME SNAPSHOT_COUNT  SNAPSHOT_SIZE
```

Verbose output is also available with `-v / --verbose`.

Each snapshot is listed with:

- snapshot name
- datetime created
- size
- list of children

```bash
$ ./lhcs.py -L -P esphome -v
NAMESPACE       PVC_NAME        PV_NAME SNAPSHOT_COUNT  SNAPSHOT_SIZE
home    esphome pvc-ef709ad6-1035-4c39-8137-4459faefd87f        15      443.8 MB
|- c-bbiyfe-4aa9d4f4    2021-11-30T10:00:03Z    442.7 MB        children {'c-bbiyfe-dbe9cc75': True}
|- c-bbiyfe-dbe9cc75    2021-12-01T10:00:02Z    0.0 MB  children {'c-bbiyfe-747aea25': True}
|- c-bbiyfe-747aea25    2021-12-02T10:00:02Z    0.0 MB  children {'c-bbiyfe-120ac85d': True}
|- c-bbiyfe-120ac85d    2021-12-03T10:00:23Z    0.0 MB  children {'c-bbiyfe-7fe9664f': True}
|- c-bbiyfe-7fe9664f    2021-12-04T10:00:29Z    0.0 MB  children {'c-bbiyfe-fa473ffd': True}
|- c-bbiyfe-fa473ffd    2021-12-05T10:00:19Z    0.0 MB  children {'c-bbiyfe-1c37a3a2': True}
|- c-bbiyfe-1c37a3a2    2021-12-06T10:00:21Z    0.0 MB  children {'c-bbiyfe-be41e86d': True}
|- c-bbiyfe-be41e86d    2021-12-07T10:00:19Z    0.0 MB  children {'c-bbiyfe-acc3104b': True}
|- c-bbiyfe-acc3104b    2021-12-08T10:00:22Z    0.0 MB  children {'c-bbiyfe-a4b6fc0c': True}
|- c-bbiyfe-a4b6fc0c    2021-12-09T10:00:21Z    0.0 MB  children {'80751413-0cb3-4532-a64a-7f1799bed460': True}
|- 80751413-0cb3-4532-a64a-7f1799bed460 2021-12-10T20:03:18Z    0.0 MB  children {'backup-20-4aa58ea-77074ba4-c-7fc5b997': True}
|- backup-20-4aa58ea-77074ba4-c-7fc5b997        2021-12-16T10:00:02Z    1.0 MB  children {'0ab41e50-c428-45d1-96bb-242d2b23174e': True}
|- 0ab41e50-c428-45d1-96bb-242d2b23174e 2022-01-11T19:01:46Z    0.0 MB  children {'f6eeee17-ba16-416e-ba59-75ce07d1490c': True}
|- f6eeee17-ba16-416e-ba59-75ce07d1490c 2022-01-11T20:55:02Z    0.0 MB  children {'e3096ad2-d004-4b76-89d5-8e779df754fb': True}
|- e3096ad2-d004-4b76-89d5-8e779df754fb 2022-01-12T22:54:46Z    0.0 MB  children {'volume-head': True}
```

Or only show snapshots which match a pattern:

```bash
./lhcs.py -L -N home -v -S c-bbiyfe
NAMESPACE       PVC_NAME        PV_NAME SNAPSHOT_COUNT  SNAPSHOT_SIZE
home    esphome pvc-ef709ad6-1035-4c39-8137-4459faefd87f        3       442.7 MB
|- c-bbiyfe-be41e86d    2021-12-07T10:00:19Z    442.7 MB        children {'c-bbiyfe-acc3104b': True}
|- c-bbiyfe-acc3104b    2021-12-08T10:00:22Z    0.0 MB  children {'c-bbiyfe-a4b6fc0c': True}
|- c-bbiyfe-a4b6fc0c    2021-12-09T10:00:21Z    0.0 MB  children {'80751413-0cb3-4532-a64a-7f1799bed460': True}
home    gitea   pvc-fe8945b2-5f1d-4dac-bc7c-c781e1fa82d6        3       253.7 MB
|- c-bbiyfe-5e1659c3    2021-12-07T10:00:18Z    207.8 MB        children {'c-bbiyfe-2f4712cc': True}
|- c-bbiyfe-2f4712cc    2021-12-08T10:00:22Z    23.0 MB children {'c-bbiyfe-6b8ea8e0': True}
|- c-bbiyfe-6b8ea8e0    2021-12-09T10:00:17Z    22.9 MB children {'0a2a046f-9dba-414d-b31a-08ab9869246d': True}

TOTAL   ALL     VOLSNAPSHOTS    6       696.4 MB
```

### Remove Snapshots

Removing snapshots is accomplished using the `-R/--remove` option.

The script will only remove the oldest snapshots there are move than the `-c/--retain-count`, which defaults to `30`.

In this case, all our volumes have 15 snapshots, more than the default retain-count, so none were deleted.

```bash
$ ./lhcs.py -R 
games/mc-creative-minecraft-bedrock: 15 snapshots
games/mc-survival-minecraft-bedrock: 15 snapshots
games/valheim-config: 15 snapshots
home/esphome: 15 snapshots
home/gitea: 15 snapshots
unifi/unifi: 15 snapshots

TOTAL: deleted 0 snapshots, combined size 0.0 MB
```

Filtering works the same as in `--list` mode using `-N / --namespace` and `-P / --pvc` flags.

A dry-run can be used to ensure than changes are not made unless desired with `-n / --dry-run`.
This example uses `--dry-run`, `--namespace` and a reduced `--retain-count` of 10.

```bash
$ ./lhcs.py -R -N games -c 14 -n
games/mc-creative-minecraft-bedrock: 15 snapshots
games/mc-creative-minecraft-bedrock: would have deleted 1 snapshots, combined size 419.3 MB
games/mc-survival-minecraft-bedrock: 15 snapshots
games/mc-survival-minecraft-bedrock: would have deleted 1 snapshots, combined size 435.1 MB
games/valheim-config: 15 snapshots
games/valheim-config: would have deleted 1 snapshots, combined size 1022.0 MB

TOTAL: would have deleted 3 snapshots, combined size 1876.4 MB

NOTE: it takes Longhorn some time to process deletions, please be patient and monitor via the dashboard.
```

You can also see `-v / --verbose` information about what is (or will be) deleted:

```bash
$ ./lhcs.py -R -P esphome -c 10 -n -v
home/esphome: 15 snapshots
would delete home/esphome/c-bbiyfe-4aa9d4f4     2021-11-30T10:00:03Z    442.7 MB
would delete home/esphome/c-bbiyfe-dbe9cc75     2021-12-01T10:00:02Z    0.0 MB
would delete home/esphome/c-bbiyfe-747aea25     2021-12-02T10:00:02Z    0.0 MB
would delete home/esphome/c-bbiyfe-120ac85d     2021-12-03T10:00:23Z    0.0 MB
would delete home/esphome/c-bbiyfe-7fe9664f     2021-12-04T10:00:29Z    0.0 MB
home/esphome: would have deleted 5 snapshots, combined size 442.7 MB
would submit purge request for home/esphome

NOTE: it takes Longhorn some time to process deletions, please be patient and monitor via the dashboard.
```

Finally here's an example of actually removing snapshots without `--dry-run`:

```bash
$ ./lhcs.py -R -N home -c 14 -v
home/esphome: 15 snapshots
deleting home/esphome/c-bbiyfe-4aa9d4f4 2021-11-30T10:00:03Z    442.7 MB
home/esphome: deleted 1 snapshots, combined size 442.7 MB
submitted purge request for home/esphome
home/gitea: 15 snapshots
deleting home/gitea/c-bbiyfe-7602cb66   2021-11-30T10:00:20Z    207.8 MB
home/gitea: deleted 1 snapshots, combined size 207.8 MB
submitted purge request for home/gitea

TOTAL: deleted 2 snapshots, combined size 650.5 MB

NOTE: it takes Longhorn some time to process deletions, please be patient and monitor via the dashboard.
```

In this example we delete some larger snapshots, then use `--dry-run` to monitor status as it's taking a while for the server to remove them.

```bash
$ ./lhcs.py -R -c 14 
games/mc-creative-minecraft-bedrock: 15 snapshots
games/mc-creative-minecraft-bedrock: deleted 1 snapshots, combined size 419.3 MB
games/mc-survival-minecraft-bedrock: 15 snapshots
games/mc-survival-minecraft-bedrock: deleted 1 snapshots, combined size 435.1 MB
games/valheim-config: 15 snapshots
games/valheim-config: deleted 1 snapshots, combined size 1022.0 MB
home/esphome: 14 snapshots
home/gitea: 14 snapshots
unifi/unifi: 15 snapshots
unifi/unifi: deleted 1 snapshots, combined size 3517.6 MB

TOTAL: deleted 4 snapshots, combined size 5394.0 MB

NOTE: it takes Longhorn some time to process deletions, please be patient and monitor via the dashboard.
$ ./lhcs.py -R -c 14 -n
games/mc-creative-minecraft-bedrock: 14 snapshots
games/mc-survival-minecraft-bedrock: 14 snapshots
games/valheim-config: 15 snapshots
games/valheim-config: would have deleted 1 snapshots, combined size 1022.0 MB
home/esphome: 14 snapshots
home/gitea: 14 snapshots
unifi/unifi: 15 snapshots
unifi/unifi: would have deleted 1 snapshots, combined size 3519.0 MB

TOTAL: would have deleted 2 snapshots, combined size 4541.0 MB

NOTE: it takes Longhorn some time to process deletions, please be patient and monitor via the dashboard.
benjamin@anguirel:~/code/longhorn-cli$ ./lhcs.py -R -c 14 -n
games/mc-creative-minecraft-bedrock: 14 snapshots
games/mc-survival-minecraft-bedrock: 14 snapshots
games/valheim-config: 14 snapshots
home/esphome: 14 snapshots
home/gitea: 14 snapshots
unifi/unifi: 14 snapshots

TOTAL: would have deleted 0 snapshots, combined size 0.0 MB
```

Or only delete snapshots which match a pattern with `-S / --snap-pattern`. Note that `retain-count` is still in effect so if wanting to delete all snapshots matching a pattern it must be set to `0`.

```bash
$ ./lhcs.py -R -N home -v -S c-bbiyfe -n -c 0
home/esphome: 3 snapshots
would delete home/esphome/c-bbiyfe-be41e86d     2021-12-07T10:00:19Z    442.7 MB
would delete home/esphome/c-bbiyfe-acc3104b     2021-12-08T10:00:22Z    0.0 MB
would delete home/esphome/c-bbiyfe-a4b6fc0c     2021-12-09T10:00:21Z    0.0 MB
home/esphome: would have deleted 3 snapshots, combined size 442.7 MB
would submit purge request for home/esphome
home/gitea: 3 snapshots
would delete home/gitea/c-bbiyfe-5e1659c3       2021-12-07T10:00:18Z    207.8 MB
would delete home/gitea/c-bbiyfe-2f4712cc       2021-12-08T10:00:22Z    23.0 MB
would delete home/gitea/c-bbiyfe-6b8ea8e0       2021-12-09T10:00:17Z    22.9 MB
home/gitea: would have deleted 3 snapshots, combined size 253.7 MB
would submit purge request for home/gitea

TOTAL: would have deleted 6 snapshots, combined size 696.4 MB

NOTE: it takes Longhorn some time to process deletions, please be patient and monitor via the dashboard.
```

The simple help docs:

```bash
usage: lhcs.py [-h] (-L | -R) [-N NAMESPACE] [-P PVC] [-n] [-c RETAIN_COUNT] [-v] [-u URL]

A client to list information about Longhorn PVCs and their snapshots, and remove snapshots when desired. --list or --remove must be used to choose a primary action.

optional arguments:
  -h, --help            show this help message and exit
  -L, --list            list PVC information
  -R, --remove          remove PVC snapshots
  -N NAMESPACE, --namespace NAMESPACE
                        limit to specified namespace
  -P PVC, --pvc PVC     limit to specified name (multiple PVCs can have the same name if in different namespaces)
  -S SNAP_PATTERN, --snap-pattern SNAP_PATTERN
                        limit to snapshot names matching this pattern
  -n, --dry-run         a dry-run will make no changes to the PVCs or snapshots
  -c RETAIN_COUNT, --retain-count RETAIN_COUNT
                        number of snapshots to retain (default: 30)
  -v, --verbose         show snapshot detail when listing and verbose info when removing
  -u URL, --url URL     longhorn API URL (default: environment value of 'LONGHORN_URL')

--url is required if 'LONGHORN_URL' is not specified in the environment. NOTE: it takes Longhorn some time to process deletions, please be patient and monitor via the dashboard.
```

Note that suggested `LONGHORN_URL` or `-u / --url` values are:

`http://longhorn-frontend.longhorn-system/v1` - when running within the kubernetes cluster

`http://localhost:8080/v1` - when running on local machine using port forward:

```bash
kubectl port-forward services/longhorn-frontend 8080:http -n longhorn-system
```

These suggestions come from the [Longhorn Python Client](https://longhorn.io/docs/1.2.3/references/longhorn-client-python/) docs.
