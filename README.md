# ludus_sheepl_role

Deterministic, server-less NPC activity for a Windows VM using
[Sheepl](https://github.com/lorentzenman/sheepl) (Matt Lorentzen, @lorentzenman). A drop-in
replacement for the GHOSTS client/server pair: instead of a central NPC server
every endpoint carries its own self-contained AutoIT activity script, so there
is nothing extra to deploy or keep healthy.

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

The `phishing` profile has the facilities-manager NPC browse the vendor portal
and intranet and then "review" the most recent document in its Downloads/intake
folder (`files/open_intake.ps1`). That open is the deterministic initial-access
foothold: benign on its own, it lands a beacon only when the operator's
submitted lure is the newest file.

## Profiles

Set `ludus_sheepl_profile` to one of these. Each is a `templates/<name>_profile.json.j2`
rendered from the role variables, so you tune behaviour with vars, not by editing
the toolkit. Pick the one that fits the lab type.

| Profile | For | What the NPC does |
|---|---|---|
| `ambient` | default / background realism | Browses the intranet and runs a little benign shell. Generic on-host noise, no foothold. |
| `phishing` | offensive, phishing initial access | Ambient browsing plus opening the newest intake document (the deterministic foothold). Needs `ludus_sheepl_portal_url` / `ludus_sheepl_intake_dir`. |
| `blue_team` | defensive / detection labs | A richer benign baseline: web browsing, routine `cmd` (whoami, ipconfig, tasklist, dir), and benign PowerShell (service/process/filesystem queries). No creds, no foothold, so it gives defenders normal activity to model and false positives to triage. |
| `red_team` | offensive, credential/lateral-movement labs | Types explicit SMB creds, lists `cmdkey`, queries SPNs (`setspn -Q */*`), and RDPs to another host with domain creds. The point is to leave harvestable credential material (cached RDP creds, LSASS) and kerberoast context for the operator. Set `ludus_sheepl_rdp_*`. |
| `responder_bait` | LLMNR/NBT-NS poisoning labs | Tries to reach a host that does not resolve (`ludus_sheepl_bad_host`), so the lookup falls back to LLMNR/NBT-NS broadcast and Responder/Inveigh can poison it and capture NetNTLMv2. Also authenticates to a real share for relay practice. |
| `ad_user` | AD telemetry, Kerberos/NTLM labs | Realistic domain usage: `klist`, SYSVOL/NETLOGON access, `gpupdate`, `net group /domain`, `nltest`, an LDAP query. Produces live Kerberos (4768/4769) and NTLM auth for both blue-team baselines and red-team recon/kerberoast context. |

`red_team`, `responder_bait`, and `ad_user` drive real domain auth, so point
`ludus_sheepl_fileserver` at the lab DC/file server, set `ludus_sheepl_domain`,
and (for `red_team`) set real `ludus_sheepl_rdp_user` / `ludus_sheepl_rdp_password`.
Placeholders still generate failed-logon telemetry, which is itself useful. These
profiles are most effective on a domain-joined endpoint, but the name-resolution
and NTLM attempts fire even off-domain, which is all `responder_bait` needs.

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
| `ludus_sheepl_profile` | `ambient` | Which bundled profile to render (see Profiles) |
| `ludus_sheepl_portal_url` | vendor portal on VLAN 10 | URL the NPC "checks" (phishing/blue_team) |
| `ludus_sheepl_intranet_url` | corporate intranet | URL the NPC browses |
| `ludus_sheepl_total_time` | `10m` | Window the task sequence spreads over |
| `ludus_sheepl_loop` | `true` | Repeat the sequence so the NPC stays active |
| `ludus_sheepl_domain` | `CORP` | Short domain name for net/nltest/klist (ad_user/red_team) |
| `ludus_sheepl_fileserver` | DC on VLAN 10 | Real SMB host the NPC authenticates to |
| `ludus_sheepl_share` | `NETLOGON` | Share for the valid auth (any domain user can read it) |
| `ludus_sheepl_bad_host` | `fileserver01` | Non-resolving host for LLMNR/NBT-NS bait (responder_bait) |
| `ludus_sheepl_rdp_target` | DC on VLAN 10 | RemoteDesktop target for red_team |
| `ludus_sheepl_rdp_user` / `_password` | `CORP\Administrator` / placeholder | Creds the red_team NPC types into mstsc |

## Example (VM `role_vars`)

```yaml
roles:
  - ludus_sheepl_role
role_vars:
  ludus_sheepl_profile: phishing
  ludus_sheepl_portal_url: "http://10.6.10.40/vendor-portal"
```

An AD endpoint that feeds a Responder/NTLM-relay lab and generates Kerberos
telemetry:

```yaml
roles:
  - ludus_sheepl_role
role_vars:
  ludus_sheepl_profile: responder_bait
  ludus_sheepl_domain: "GLASSHOUSE"
  ludus_sheepl_fileserver: "10.6.10.10"   # the lab DC
  ludus_sheepl_bad_host: "backup-fs"      # does not resolve -> LLMNR/NBT-NS
```
