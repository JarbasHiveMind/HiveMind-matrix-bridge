# Setup Walkthrough

This walkthrough takes you from nothing to a working Matrix chatbot backed by a HiveMind hub.

## How the bridge fits together

The bridge is a HiveMind satellite. It holds two connections at once:

- **To Matrix** — it logs in with a bot access token, joins a room, and listens for messages.
- **To the HiveMind hub** — it authenticates with a HiveMind access key and password, then exchanges encrypted protocol messages.

When a room message mentions the bot, the bridge sends a `recognizer_loop:utterance` to the hub and waits for a `speak` reply, which it posts back to the room.

```
Matrix room  ⇄  bridge  ⇄  hivemind-core hub  ⇄  OVOS pipeline / skills
```

## Step 1 — Stand up a HiveMind hub

Install and run [hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core) on a machine reachable from the bridge:

```bash
pip install hivemind-core
hivemind-core listen
```

By default the hub listens on port `5678`.

## Step 2 — Register the bridge as a client

On the hub machine, issue credentials for the bridge:

```bash
hivemind-core add-client --name matrix-bridge \
  --access-key "your-access-key" --password "your-password"
```

Keep the access key and password; the bridge authenticates with them. List existing clients with `hivemind-core list-clients`.

## Step 3 — Create a Matrix bot account

1. Register a Matrix account for the bot on any homeserver (`matrix.org` or self-hosted).
2. Log in once with a client such as [Element](https://element.io).
3. Copy the account's **access token** (Element: *Settings → Help & About → Access Token*).
4. Create or pick a room, note its alias (for example `#hivemind-bots:matrix.org`), and invite the bot account into it.

## Step 4 — Install the bridge

```bash
pip install git+https://github.com/JarbasHiveMind/HiveMind-matrix-bridge
```

## Step 5 — Provide the HiveMind credentials

Either store an identity once:

```bash
hivemind-client set-identity \
  --key "your-access-key" \
  --password "your-password" \
  --host "ws://192.168.1.100"
```

or pass `--key/--password/--host` on each run.

## Step 6 — Run

```bash
HiveMind-matrix run \
  --botname thehivebot \
  --matrixtoken "syt_your_access_token" \
  --matrixhost "https://matrix.org" \
  --room "#hivemind-bots:matrix.org"
```

You should see the bridge log `connected to Matrix` and `connected to HiveMind`.

## Step 7 — Talk to it

In the room, mention the bot:

```
thehivebot what is the weather?
```

The bridge forwards the text after the mention to the hub and posts the spoken answer back.
