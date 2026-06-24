# Examples

## Run with stored identity

Store the HiveMind identity once, then run with only Matrix options:

```bash
hivemind-client set-identity --key KEY --password PASS --host ws://192.168.1.100
HiveMind-matrix run \
  --botname thehivebot \
  --matrixtoken "syt_..." \
  --room "#hivemind-bots:matrix.org"
```

## Run with all credentials inline

Useful for containers or one-off runs where no identity file exists:

```bash
HiveMind-matrix run \
  --botname thehivebot \
  --matrixtoken "syt_..." \
  --matrixhost "https://matrix.org" \
  --room "#hivemind-bots:matrix.org" \
  --key "your-access-key" \
  --password "your-password" \
  --host "192.168.1.100" \
  --port 5678
```

A `ws://` prefix is added to `--host` automatically when no scheme is given.

## A conversation

Once running, anyone in the room invokes the bot by mentioning it:

```
alice> thehivebot what time is it?
thehivebot> It is half past three.

alice> thehivebot set a timer for five minutes
thehivebot> Timer set for five minutes.
```

Messages that do not mention `thehivebot` are ignored.

## Embed the bridge in your own program

`HiveMindMatrixBridge` is an asyncio object. The hub and Matrix clients can be injected for testing or customization:

```python
import asyncio
from hm_matrix_bridge import HiveMindMatrixBridge

async def main():
    bridge = HiveMindMatrixBridge(
        matrix_host="https://matrix.org",
        matrix_token="syt_...",
        room_alias="#hivemind-bots:matrix.org",
        bot_mention="thehivebot",
        key="your-access-key",
        password="your-password",
        host="ws://192.168.1.100",
        port=5678,
        response_timeout=30.0,
    )
    await bridge.start()
    try:
        await asyncio.Event().wait()  # run until cancelled
    finally:
        await bridge.stop()

asyncio.run(main())
```
