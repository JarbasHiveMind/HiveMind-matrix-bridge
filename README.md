# HiveMind Matrix Bridge

Relay a [Matrix](https://matrix.org) chatroom to a [HiveMind](https://github.com/JarbasHiveMind/HiveMind-core) hub.

The bridge is a HiveMind **satellite**. Its input and output are a Matrix room instead of a microphone. Messages that mention the bot go to the hub as utterances. The hub's spoken reply posts back into the room. This turns any HiveMind hub, and the OVOS skills behind it, into a Matrix chatbot.

```
Matrix room  ⇄  HiveMind-matrix-bridge  ⇄  HiveMind hub (hivemind-core)  ⇄  OVOS skills
```

## Prerequisites

- A running **HiveMind hub** ([hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core)) you can reach over the network.
- A **HiveMind access key and password** for this bridge, issued by the hub with `hivemind-core add-client` (see [Quickstart](#quickstart)).
- A **Matrix account** for the bot and an **access token** for it. Any homeserver works (`matrix.org` or self-hosted). Create the account, log in once, and copy its access token (in Element: *Settings → Help & About → Access Token*).
- The room alias the bot should join, for example `#hivemind-bots:matrix.org`. Invite the bot account to that room.

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

Note the access key and password. The bridge needs them to authenticate.

A new client is registered but mute: the hub denies every message type until you whitelist it. Run this too, or the bridge will connect and never do anything:

```bash
hivemind-core allow-msg recognizer_loop:utterance matrix-bridge
hivemind-core allow-msg speak matrix-bridge
```

If you are running more than one bridge on the same host (Matrix, Mattermost, DeltaChat, HackChat side by side), give each one its own `hivemind-client set-identity` credentials and, if applicable, its own config directory. Bridges that share an identity share a Noise session pin, and the hub will treat reconnects from either one as the same client, which breaks encryption for both.

**2. Store the HiveMind credentials** so they are read automatically:

```bash
hivemind-client set-identity \
  --key "your-access-key" \
  --password "your-password" \
  --host "ws://192.168.1.100"
```

`set-identity` ships with `hivemind-bus-client`, a dependency of this bridge. You can instead pass `--key/--password/--host` on every run, without storing an identity.

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
| `--botname` | Mention prefix that triggers the bot | none |
| `--matrixtoken` | Matrix access token for the bot account | none |
| `--matrixhost` | Matrix homeserver URL | `https://matrix.org` |
| `--room` | Room alias to join | `#hivemind-bots:matrix.org` |
| `--key` | HiveMind access key | read from identity file |
| `--password` | HiveMind password | read from identity file |
| `--host` | HiveMind host (a `ws://` prefix is added if no scheme) | read from identity file |
| `--port` | HiveMind port | `5678` |

When `--key/--password/--host` are omitted, the bridge reads them from the stored `NodeIdentity`. If none of the three are available, the bridge exits with an error that points you at `hivemind-client set-identity`.

## Troubleshooting

- **`NodeIdentity not set`**: run `hivemind-client set-identity`, or pass `--key/--password/--host` explicitly.
- **Bot ignores messages**: the message must contain `--botname` exactly. Messages without the mention are dropped by design.
- **Reply is the literal text `Error`**: the hub did not return a `speak` within the response timeout (30s). Confirm the hub is reachable, the access key is authorized, and an OVOS pipeline produces spoken answers.
- **Connection refused or no reply**: verify `--host` and `--port` point at the running hub, and that the bridge's access key is registered (`hivemind-core list-clients`).
- **Bridge connects but the room never gets a reply**: the client is registered but not whitelisted. Run `hivemind-core allow-msg recognizer_loop:utterance matrix-bridge` and `hivemind-core allow-msg speak matrix-bridge` on the hub.
- **`invalid api key` at connect time**: the hub rejected the handshake, usually because the bridge (or `hivemind-bus-client`) is older than the hub. Upgrade the bridge.
- **"reconnect worker already running" in the bridge log**: a known issue in older `hivemind-bus-client` releases when a connection drops and retries overlap. It is fixed upstream; upgrade `hivemind-bus-client` and the bridge.
- **Handshake fails after the hub was reinstalled or the client's key changed**: the bridge is holding a stale Noise session pin from a previous run. Clear it on the hub with `hivemind-core reset-noise-pin matrix-bridge` and restart the bridge.

## Documentation

- **[Setup walkthrough](docs/setup.md)**: a full path from an empty machine to a running bridge.
- **[Operator setup](docs/operator-setup.md)**: get the bot's Matrix account and access token (or self-host a homeserver), register the bridge on a HiveMind hub, run it, and check the live end-to-end test.
- **[Configuration reference](docs/configuration.md)**: every option, credential, and default.
- **[Examples](docs/examples.md)**: sample runs and embedding the bridge in your own program.

## Related projects

- [HiveMind-core](https://github.com/JarbasHiveMind/HiveMind-core): the HiveMind hub this bridge connects to.
- [hivemind-bus-client](https://github.com/JarbasHiveMind/hivemind-bus-client): the client library that provides `set-identity` and the HiveMind connection.

## License

See [LICENSE](LICENSE).
