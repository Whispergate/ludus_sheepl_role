# ludus_sheepl_role

Deterministic, server-less NPC activity for a Windows VM using
[Sheepl](https://github.com/Whispergate/sheepl) (fork of Matt Lorentzen's
original). A drop-in replacement for the GHOSTS client/server pair: instead of a
central NPC server every endpoint carries its own self-contained AutoIT activity
script, so there is nothing extra to deploy or keep healthy.

## What it does

1. Renders a Sheepl JSON profile (`ambient` by default, or one of the other
   profiles in the table below) from the role variables.
2. Runs Sheepl on the Ansible control node (`delegate_to: localhost`, python3)
   to turn that profile into an AutoIT `.au3` activity script. The toolkit is
   vendored under `files/sheepl/`, so no network fetch is needed.
3. Installs the AutoIT runtime on the Windows target (only if absent).
4. Ships the activity script plus the intake handler and registers a scheduled
   task that runs the script **as the autologon NPC** at logon (interactive
   token, no stored password).

The `phishing` profile has the NPC browse the vendor portal (triggering a
payload download) and then "review" the most recent document in its Downloads
folder (`files/open_intake.ps1`). That open is the deterministic initial-access
foothold: benign on its own, it lands a beacon only when the operator's staged
payload is the newest file.

## Profiles

Set `ludus_sheepl_profile` to one of these. Each is a `templates/<name>_profile.json.j2`
rendered from the role variables, so you tune behaviour with vars, not by editing
the toolkit.

| Profile | For | What the NPC does |
|---|---|---|
| `ambient` | default / background realism | Browses the intranet, runs benign shell commands. Generic noise, no foothold. |
| `phishing` | offensive, phishing initial access | Browses the portal URL (downloads the operator's staged payload), runs `open_intake.ps1` (opens it), browses the intranet. |
| `blue_team` | defensive / detection labs | Richer benign baseline: web browsing, routine cmd/PowerShell (whoami, ipconfig, tasklist, services). No creds or foothold. |
| `red_team` | credential/lateral-movement labs | Types explicit SMB creds, lists cmdkey, queries SPNs, RDPs to another host. Leaves harvestable cred material and kerberoast context. |
| `responder_bait` | LLMNR/NBT-NS poisoning labs | Tries to reach a non-resolving host so the lookup falls back to broadcast; Responder/Inveigh can poison it. |
| `ad_user` | AD telemetry, Kerberos/NTLM labs | Realistic domain usage: klist, SYSVOL/NETLOGON access, gpupdate, nltest, LDAP queries. |
| `analyst` | SOC / IR labs | Browses threat intel sites, checks security event logs, opens a KeePass vault, tracks IOCs in a spreadsheet. |
| `chief` | noisy admin / lateral-movement labs | Like red_team + responder_bait combined: shell diagnostics, RDP, failed name resolution, SPN notes in clipboard. |
| `developer` | software / DevOps scenarios | Runs git/npm/dotnet builds, opens Word docs, browses dev sites, drafts emails. API tokens in clipboard. |
| `executive` | phishing target / whaling labs | Browses news/LinkedIn, writes board memos in Word, opens Outlook, watches media in VLC. |
| `helpdesk` | tier-1 support / lateral-movement | Manages users, RDPs to endpoints with subtask commands, opens Computer Management, writes incident notes. |
| `sysadmin` | privileged access / AD labs | AD PowerShell queries, nltest, SSHs into a Linux host, opens KeePass domain-creds vault. Service account creds in clipboard. |
| `technician` | OT / field-tech scenarios | Network diagnostics, WMI queries, SSHs to OT devices, writes maintenance logs, tracks assets in a spreadsheet. |
| `crossplatform` | general office productivity | Browses the intranet, writes docs in LibreOffice, maintains a spreadsheet, plays media in VLC. |

## Variable groups by profile

**All profiles** use: `ludus_sheepl_name`, `ludus_sheepl_total_time`, `ludus_sheepl_typing_speed`, `ludus_sheepl_loop`, `ludus_sheepl_tray_icon`.

| Variable group | Profiles that need it |
|---|---|
| `ludus_sheepl_intranet_url` | ambient, phishing, blue_team, analyst, chief, developer, executive, sysadmin, crossplatform |
| `ludus_sheepl_portal_url` | phishing, blue_team, chief |
| `ludus_sheepl_domain` | ad_user, sysadmin |
| `ludus_sheepl_fileserver` / `_share` | ad_user, red_team, responder_bait |
| `ludus_sheepl_bad_host` | responder_bait, chief |
| `ludus_sheepl_rdp_*` | red_team, chief, helpdesk |
| `ludus_sheepl_ssh_*` | sysadmin, technician |
| `ludus_sheepl_keepass_password` | analyst, sysadmin |

## Requirements

- Windows target that **autologons** the NPC user (set `windows.autologon` to
  the NPC so the logon trigger fires in a live session). Non-Windows hosts are a
  no-op.
- python3 on the Ansible control node (Ludus already has it).
- Internet reachable from the target at deploy time to fetch the AutoIT
  installer (the lab's `testing.block_internet` is applied after deploy).

## Key variables (see `defaults/main.yml`)

| Variable | Default | Purpose |
|---|---|---|
| `ludus_sheepl_npc_user` | VM autologon user | Whose session runs the activity |
| `ludus_sheepl_profile` | `ambient` | Which bundled profile to render |
| `ludus_sheepl_portal_url` | vendor portal on VLAN 10 | URL the NPC browses (phishing: triggers download) |
| `ludus_sheepl_intranet_url` | corporate intranet | URL the NPC browses for ambient noise |
| `ludus_sheepl_total_time` | `10m` | Window the task sequence spreads over |
| `ludus_sheepl_loop` | `true` | Repeat the sequence so the NPC stays active |
| `ludus_sheepl_domain` | `CORP` | Short domain name for net/nltest/klist |
| `ludus_sheepl_fileserver` | DC on VLAN 10 | Real SMB host the NPC authenticates to |
| `ludus_sheepl_share` | `NETLOGON` | Share for the valid auth |
| `ludus_sheepl_bad_host` | `fileserver01` | Non-resolving host for LLMNR/NBT-NS bait |
| `ludus_sheepl_rdp_target` | DC on VLAN 10 | RemoteDesktop target |
| `ludus_sheepl_rdp_user` / `_password` | `CORP\Administrator` / placeholder | Creds the NPC types into mstsc |
| `ludus_sheepl_ssh_target` | same as fileserver | PuttyConnection target |
| `ludus_sheepl_ssh_user` / `_password` | `root` / placeholder | SSH creds for PuttyConnection |
| `ludus_sheepl_keepass_password` | `MasterK3y!Vault` | KeePass master password (typed live, harvestable) |

## Example (VM `role_vars`)

```yaml
roles:
  - whispergate.ludus_sheepl_role
role_vars:
  ludus_sheepl_profile: phishing
  ludus_sheepl_portal_url: "http://10.6.70.40/vendor-portal/contract-review"
  ludus_sheepl_intranet_url: "http://10.6.10.10"
```

A sysadmin that generates AD and SSH telemetry:

```yaml
roles:
  - whispergate.ludus_sheepl_role
role_vars:
  ludus_sheepl_profile: sysadmin
  ludus_sheepl_domain: "GLASSHOUSE"
  ludus_sheepl_ssh_target: "10.6.40.10"
  ludus_sheepl_ssh_user: "operator"
  ludus_sheepl_ssh_password: "fieldOps!2026"
  ludus_sheepl_keepass_password: "Vault#Master1"
```

A responder-bait endpoint for LLMNR/NTLM-relay:

```yaml
roles:
  - whispergate.ludus_sheepl_role
role_vars:
  ludus_sheepl_profile: responder_bait
  ludus_sheepl_domain: "GLASSHOUSE"
  ludus_sheepl_fileserver: "10.6.10.10"
  ludus_sheepl_bad_host: "backup-fs"
```
