# Configuration & Credentials Reference

The bridge needs two sets of credentials: one for Matrix, one for the HiveMind hub.

## Matrix credentials

| Option | Meaning |
| --- | --- |
| `--matrixhost` | Homeserver base URL, for example `https://matrix.org`. Default `https://matrix.org`. |
| `--matrixtoken` | Access token for the bot account. Get it from a logged-in Matrix client. |
| `--room` | Alias of the room to join, for example `#hivemind-bots:matrix.org`. The bot account must be a member. |
| `--botname` | Mention prefix that triggers the bot. The bridge processes only messages that contain this string. |

The bot strips the mention before it sends the rest of the message to the hub. It recognizes the forms `@botname`, `botname:`, and bare `botname`.

## HiveMind credentials

| Option | Meaning | Default |
| --- | --- | --- |
| `--key` | HiveMind access key, from `hivemind-core add-client`. | read from identity file |
| `--password` | HiveMind password, from `hivemind-core add-client`. | read from identity file |
| `--host` | Hub host. A `ws://` prefix is added automatically if you omit the scheme. | read from identity file |
| `--port` | Hub port. | `5678` |

### Identity file

When `--key/--password/--host` are not passed, the bridge reads them from the stored `NodeIdentity`. Set it once with:

```bash
hivemind-client set-identity \
  --key "your-access-key" \
  --password "your-password" \
  --host "ws://192.168.1.100"
```

If neither the options nor a stored identity supply a key, password, and host, the bridge raises:

```
NodeIdentity not set, please pass key/password/host or call 'hivemind-client set-identity'
```

## Response timeout

The bridge waits up to 30 seconds for the hub's `speak` reply. On timeout it posts the literal text `Error` to the room. The timeout is a constructor argument, `response_timeout`, on `HiveMindMatrixBridge` for programmatic use.

## Encryption

The HiveMind connection is authenticated and encrypted at the protocol layer, handled by `hivemind-bus-client`. The Matrix connection uses the homeserver's HTTPS endpoint. The underlying client library does not support end-to-end encrypted Matrix rooms. Use an unencrypted room.

---
[← Operator setup](operator-setup.md) · [Home](../README.md) · [Examples →](examples.md)
