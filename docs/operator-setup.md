# Operator setup: running the Matrix bridge

This bridge logs a bot into a **Matrix room** and relays each mention to and
from a HiveMind hub. This turns any HiveMind hub, and the OVOS skills behind
it, into a Matrix chatbot. As an operator you need a **Matrix account for the
bot** with an **access token**, a **room** to join, and a HiveMind hub to
point it at.

```
Matrix user  ⇄  Matrix room (homeserver)  ⇄  HiveMind-matrix  ⇄  HiveMind hub  ⇄  OVOS skills
```

## 1. Get the bot a Matrix account and access token

You need a Matrix **account on a homeserver** and an **access token** for it.

### Option A: a public homeserver (quickest)

Register a bot account on a public homeserver such as `matrix.org` and copy its
access token:

- **Via Element** (web/desktop): log in as the bot account, then go to
  *Settings → Help & About → Advanced → Access Token*. Copy the token. It looks
  like `syt_…`.
- **Via the login API** (no client):

  ```bash
  curl -XPOST 'https://matrix.org/_matrix/client/v3/login' -d '{
    "type": "m.login.password",
    "identifier": {"type": "m.id.user", "user": "thehivebot"},
    "password": "the-bot-password"
  }'
  ```

  The JSON response contains `access_token`.

### Option B: self-hosted homeserver (no external account)

Run your own homeserver in a container, **Conduit** (a single small binary) or
**Synapse**. Register the bot user and get its token the same way. This is
the no-external-account path, and it is the basis for the full Matrix-loop
test (see the TODO in `tests/e2e/test_matrix_bridge_e2e.py`).

Then **create or pick a room**, note its alias (for example
`#hivemind-bots:matrix.org`), and **invite the bot account** to it.

## 2. Prerequisites

- The bot's **access token**, **homeserver URL**, and target **room alias**.
- A running **HiveMind hub** (`hivemind-core`) you can reach.
- Python 3.10 or later. `matrix-client` is a hard dependency, installed with the bridge.

## 3. Register the bridge on the hub

On the hub, create a client credential for this bridge:

```bash
hivemind-core add-client          # prints an ACCESS KEY and a PASSWORD
```

Note the **access key**, **password**, and the hub **host** and **port**
(default WebSocket port `5678`). The bridge connects as a HiveMind *satellite*
with these.

This bridge reads its HiveMind identity from disk. It has no
`--key/--password` flags of its own, so store the credentials once:

```bash
hivemind-client set-identity \
  --key      "your-access-key" \
  --password "your-hivemind-password" \
  --host     "ws://your-hub-host"
```

`set-identity` ships with `hivemind-bus-client`, a dependency of this bridge.

## 4. Install and run the bridge

```bash
pip install .          # provides the `HiveMind-matrix` command

HiveMind-matrix run \
  --botname     thehivebot \
  --matrixtoken "syt_your_access_token" \
  --matrixhost  "https://matrix.org" \
  --room        "#hivemind-bots:matrix.org"
```

Flags (verify with `HiveMind-matrix run --help`):

| Flag | Meaning | Default |
| --- | --- | --- |
| `--botname` | mention prefix that triggers the bot | none |
| `--matrixtoken` | Matrix access token for the bot account | none |
| `--matrixhost` | homeserver URL | `https://matrix.org` |
| `--room` | room alias to join | `#hivemind-bots:matrix.org` |

The HiveMind connection (key, password, host, port, default `5678`) comes from
the stored `NodeIdentity` set in step 3.

## 5. Talk to it

In the joined room, mention the bot:

```
thehivebot what time is it?
```

The bridge strips the mention, forwards the rest to the hub as a
`recognizer_loop:utterance`, waits for the hub's `speak`, and posts it back to
the room.

## Security notes

The **access token** and the **HiveMind password** are secrets. Pass them via
environment variables or a secrets manager, never in shell history or a
committed file. A token grants full control of the bot account. Revoke it
(*Settings → Sessions → sign out*) if it leaks.

Anyone in the room who mentions the bot can reach the hub. Restrict access at
the hub with client ACLs or `allowed_types`.

A freshly registered client is denied every message type by default. If you
skipped this in step 3, do it now, or the bridge connects and never replies:

```bash
hivemind-core allow-msg recognizer_loop:utterance matrix-bridge
hivemind-core allow-msg speak matrix-bridge
```

## Testing (live e2e)

`tests/e2e/test_matrix_bridge_e2e.py` runs the **real HiveMind round-trip**
unconditionally. It boots a real `hivemind-core` hub over a loopback
WebSocket and drives the production bridge and `HiveMindSolver` through it.
Only the Matrix transport is mocked, so no Matrix account or environment
variables are needed:

```bash
pytest tests/e2e/test_matrix_bridge_e2e.py
```

A **full Matrix-loop** test is the natural follow-up: boot a containerized
Conduit or Synapse homeserver, register a bot and room, post a real Matrix
message, and assert the reply lands back in the room. It is the only mocked
seam left, and it is noted as a `TODO` in that test file.

---
[← Setup walkthrough](setup.md) · [Home](../README.md) · [Configuration →](configuration.md)
