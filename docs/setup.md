# Setup walkthrough

This walkthrough takes you from nothing to a working Matrix chatbot backed by a HiveMind hub.

## How the bridge fits together

The bridge is a HiveMind satellite. It holds two connections at once:

- **To Matrix**: it logs in with a bot access token, joins a room, and listens for messages.
- **To the HiveMind hub**: it authenticates with a HiveMind access key and password, then exchanges encrypted protocol messages.

When a room message mentions the bot, the bridge sends a `recognizer_loop:utterance` to the hub. It waits for a `speak` reply, then posts the reply back to the room.

```
Matrix room  ⇄  bridge  ⇄  hivemind-core hub  ⇄  OVOS pipeline / skills
```

## Step 1: stand up a HiveMind hub

Install and run [hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core) on a machine the bridge can reach:

```bash
pip install hivemind-core
hivemind-core listen
```

By default the hub listens on port `5678`.

## Step 2: register the bridge as a client

On the hub machine, issue credentials for the bridge:

```bash
hivemind-core add-client --name matrix-bridge \
  --access-key "your-access-key" --password "your-password"
```

Keep the access key and password. The bridge authenticates with them. List existing clients with `hivemind-core list-clients`.

A freshly registered client can connect, but the hub will not act on anything it sends until you whitelist its message types. This step is easy to miss, and a skipped one is the most common reason a bridge "connects but does nothing":

```bash
hivemind-core allow-msg recognizer_loop:utterance matrix-bridge
hivemind-core allow-msg speak matrix-bridge
```

The first line lets the bridge send utterances into the hub. The second lets the hub's spoken replies come back out to the bridge. Without both, the bridge sits there connected and silent.

## Step 3: create a Matrix bot account

1. Register a Matrix account for the bot on any homeserver (`matrix.org` or self-hosted).
2. Log in once with a client such as [Element](https://element.io).
3. Copy the account's **access token** (Element: *Settings → Help & About → Access Token*).
4. Create or pick a room, note its alias (for example `#hivemind-bots:matrix.org`), and invite the bot account into it.

## Step 4: install the bridge

```bash
pip install git+https://github.com/JarbasHiveMind/HiveMind-matrix-bridge
```

## Step 5: provide the HiveMind credentials

Either store an identity once:

```bash
hivemind-client set-identity \
  --key "your-access-key" \
  --password "your-password" \
  --host "ws://192.168.1.100"
```

or pass `--key/--password/--host` on each run.

## Step 6: run

```bash
HiveMind-matrix run \
  --botname thehivebot \
  --matrixtoken "syt_your_access_token" \
  --matrixhost "https://matrix.org" \
  --room "#hivemind-bots:matrix.org"
```

You should see the bridge log `connected to Matrix` and `connected to HiveMind`.

## Step 7: talk to it

In the room, mention the bot:

```
thehivebot what is the weather?
```

The bridge forwards the text after the mention to the hub and posts the spoken answer back.

---
[Home](../README.md) · [Operator setup →](operator-setup.md)
