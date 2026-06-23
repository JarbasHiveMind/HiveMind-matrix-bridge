# HiveMind Matrix Bridge

Relay a [Matrix](https://matrix.org) chatroom to a [HiveMind](https://github.com/JarbasHiveMind/HiveMind-core) hub.

The bridge is a HiveMind **satellite** whose input and output are a Matrix room instead of a microphone. Messages that mention the bot are forwarded to the hub as utterances; the hub's spoken reply is posted back into the room. This turns any HiveMind hub (and the OVOS skills behind it) into a Matrix chatbot.

```
Matrix room  ⇄  HiveMind-matrix-bridge  ⇄  HiveMind hub (hivemind-core)  ⇄  OVOS skills
```

## Prerequisites

- A running **HiveMind hub** ([hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core)) you can reach over the network.
- A **HiveMind access key + password** for this bridge, issued by the hub with `hivemind-core add-client` (see [Quickstart](#quickstart)).
- A **Matrix account** for the bot and an **access token** for it. Any homeserver works (`matrix.org` or self-hosted). Create the account, log in once, and copy its access token (in Element: *Settings → Help & About → Access Token*).
- The room alias the bot should join (for example `#hivemind-bots:matrix.org`); invite the bot account to that room.

## Install

```bash
pip install git+https://github.com/JarbasHiveMind/HiveMind-matrix-bridge
```

Or from a checkout:

```bash
git clone https://github.com/JarbasHiveMind/HiveMind-matrix-bridge
cd HiveMind-matrix-bridge
pip install .
```

This installs the `HiveMind-matrix` console command.

## Quickstart

**1. Register the bridge on the hub** (run where `hivemind-core` is installed):

```bash
hivemind-core add-client --name matrix-bridge \
  --access-key "your-access-key" --password "your-password"
```

Note the access key and password — the bridge needs them to authenticate.

**2. Store the HiveMind credentials** so they are read automatically:

```bash
hivemind-client set-identity \
  --key "your-access-key" \
  --password "your-password" \
  --host "ws://192.168.1.100"
```

(`set-identity` ships with `hivemind-bus-client`, a dependency of this bridge.) Alternatively, pass `--key/--password/--host` on every run instead of storing an identity.

**3. Run the bridge:**

```bash
HiveMind-matrix run \
  --botname thehivebot \
  --matrixtoken "syt_your_access_token" \
  --matrixhost "https://matrix.org" \
  --room "#hivemind-bots:matrix.org"
```

**4. Send a message.** In the joined room, mention the bot:

```
thehivebot what time is it?
```

The bridge strips the mention, forwards `what time is it?` to the hub, waits for the hub's `speak` reply, and posts it back to the room.

## Configuration

`HiveMind-matrix run` options:

| Option | Description | Default |
| --- | --- | --- |
| `--botname` | Mention prefix that triggers the bot | — |
| `--matrixtoken` | Matrix access token for the bot account | — |
| `--matrixhost` | Matrix homeserver URL | `https://matrix.org` |
| `--room` | Room alias to join | `#hivemind-bots:matrix.org` |
| `--key` | HiveMind access key | read from identity file |
| `--password` | HiveMind password | read from identity file |
| `--host` | HiveMind host (a `ws://` prefix is added if no scheme) | read from identity file |
| `--port` | HiveMind port | `5678` |

When `--key/--password/--host` are omitted they are read from the stored `NodeIdentity`. If none of the three are available the bridge exits with an error pointing you at `hivemind-client set-identity`.

## Troubleshooting

- **`NodeIdentity not set`** — run `hivemind-client set-identity`, or pass `--key/--password/--host` explicitly.
- **Bot ignores messages** — the message must contain `--botname` exactly; messages without the mention are dropped by design.
- **Reply is the literal text `Error`** — the hub did not return a `speak` within the response timeout (30s). Confirm the hub is reachable, the access key is authorized, and an OVOS pipeline is producing spoken answers.
- **Connection refused / no reply** — verify `--host` and `--port` point at the running hub, and that the bridge's access key is registered (`hivemind-core list-clients`).

## Documentation

- **[Operator setup](docs/operator-setup.md)** — getting the bot's Matrix account + access token (or self-hosting a homeserver), registering the bridge on a HiveMind hub, the run command, and live e2e.

See also [`docs/`](docs/) for a full setup walkthrough, a credential reference, and worked examples.
