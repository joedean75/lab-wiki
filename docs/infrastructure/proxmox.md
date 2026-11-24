# Proxmox

## How it works

**Proxmox VE** is a Debian-based hypervisor for a home or office server. It runs two kinds of guest:

| Guest | What it is | Used here |
|---|---|---|
| **VM** (QEMU/KVM) | A full virtual machine with its own kernel. | — |
| **CT** (LXC container) | Processes isolated on the host's kernel; light and fast. | Yes |

Since Proxmox 9, an LXC container can be created **directly from an OCI image** (an "application
container"): Proxmox unpacks the image's layers into the container's disk and runs the image's
entrypoint with its environment — no Docker inside. That is how `davinci` runs.

### The home server

| Item | Value |
|---|---|
| Host | `<pve-host>`, web UI and API on **:8006** (HTTPS, self-signed) |
| Node | `server` (a second node, `mini`, is listed but was not answering) |
| Version | Proxmox VE 9.2.2 |
| CPU | Intel Xeon E3-1240 v3, 4 cores / 8 threads, no GPU |
| RAM | 15.6 GB |
| Storage | `local` (directory: ISOs, container templates `vztmpl`, imports, backups, ~81 GB free) and `local-lvm` (LVM-thin: container and VM disks, ~427 GB free) |
| Network | bridge `vmbr0`, LAN `<lan>/24` |

### Guests

| CTID | Name | Image | IP | State |
|---|---|---|---|---|
| 100 | `davinci` | `davinci-llamacpp.tar` (assistant **v1**, 2B) | <llm-host> | **stopped**, start-on-boot off — kept for rollback |
| 101 | `davinci` | `davinci-v2.tar` (assistant **v2**, 4B) | <llm-host> | **running**, start-on-boot on |
| 102 or 103 (alternates with each update) | `wiki` | `lab-wiki-<tag>.tar` (this site, [runbook](wiki-deploy.md)) | **<wiki-host>** | running, start-on-boot on |

### Unprivileged containers

All containers are **unprivileged**: root inside the container is mapped to an ordinary high user
id on the host, so a breakout lands as nobody. Files a container reads from the host must be
world-readable.

### The API and tokens

Everything in the web UI is also a REST API under `https://<host>:8006/api2/json/`. Scripts
authenticate with an **API token**, sent as a header:

```text
Authorization: PVEAPIToken=<user>@<realm>!<token-name>=<secret>
```

Here the token is `root@pam!cluade`; the full value is kept in the Windows environment variable
**`PVE_TOKEN`** (never written to files or this wiki). The certificate is self-signed, so use
`curl -k`; Windows PowerShell 5.1's `Invoke-RestMethod` fails the TLS handshake — use `curl` from Git
Bash or `curl.exe`.

Long operations (create, start, upload) return a **UPID** task id; poll
`/nodes/<node>/tasks/<UPID>/status` until `status` is `stopped`, then check `exitstatus` (`OK` or
`WARNINGS: n`).

## How to use it (API recipes)

```bash
B=https://<pve-host>:8006/api2/json
H="Authorization: PVEAPIToken=$PVE_TOKEN"

curl -sk -H "$H" $B/nodes                                   # nodes
curl -sk -H "$H" $B/nodes/server/lxc                        # containers
curl -sk -H "$H" $B/nodes/server/lxc/101/config             # one container's config
curl -sk -H "$H" $B/nodes/server/lxc/101/status/current     # running? memory? disk?
curl -sk -H "$H" "$B/nodes/server/storage/local/content?content=vztmpl"   # templates
curl -sk -H "$H" $B/cluster/nextid                          # next free CTID

# upload an OCI image as a container template
curl -sk -H "$H" -F content=vztmpl -F "filename=@davinci-v2.tar" $B/nodes/server/storage/local/upload

# create a container from it (stopped)
curl -sk -H "$H" -X POST $B/nodes/server/lxc \
  --data-urlencode vmid=101 --data-urlencode hostname=davinci \
  --data-urlencode ostemplate=local:vztmpl/davinci-v2.tar \
  --data-urlencode rootfs=local-lvm:8 --data-urlencode memory=6144 --data-urlencode swap=512 \
  --data-urlencode cores=8 --data-urlencode unprivileged=1 --data-urlencode onboot=0 \
  --data-urlencode "net0=name=eth0,bridge=vmbr0,host-managed=1,ip=<llm-host>/24,type=veth"

# start / shutdown / stop
curl -sk -H "$H" -X POST $B/nodes/server/lxc/101/status/start
curl -sk -H "$H" -X POST --data timeout=30 $B/nodes/server/lxc/101/status/shutdown

# change settings (env applies at next start)
curl -sk -H "$H" -X PUT --data onboot=1 $B/nodes/server/lxc/101/config
```

### Editing a container's environment

The `env` setting is one string with entries separated by **NUL bytes** (`\0`), not spaces (the API
displays them joined). Read it, change one entry, URL-encode it and PUT it back, then restart:

```bash
curl -sk -H "$H" $B/nodes/server/lxc/101/config | python3 -c "
import json,sys,urllib.parse
e=json.load(sys.stdin)['data']['env'].split(chr(0))
e=[('LLAMA_ARG_THREADS=4' if x.startswith('LLAMA_ARG_THREADS=') else x) for x in e]
sys.stdout.write('env='+urllib.parse.quote(chr(0).join(e),safe=''))" > env_body
curl -sk -H "$H" -X PUT $B/nodes/server/lxc/101/config --data-binary @env_body
```

### Gotchas

- Creating from an OCI image warns "Systemd 255 detected. You may need to enable nesting." — harmless
  for an application container (there is no systemd inside).
- Settings baked into the image (env) are copied at creation; anything you added to an older container
  by hand (`LLAMA_ARG_REASONING=off`) has to be copied to the new one.
- Two containers with the same IP must never run together: stop one before starting the other, and
  give only one start-on-boot.
