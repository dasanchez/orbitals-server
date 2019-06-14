# orbitals-server

This is the WebSockets server for the Orbitals game.

Try a live demo at [urra.ca](https://urra.ca/orbitals/)!

## Requirements

- Python >= 3.6 
- [websockets](https://websockets.readthedocs.io/en/stable/) library.

## Usage

To start the server, run:

```
python or_server.py
```

### Options

`-p [x]` or `--port [x]`

Listen on port x. Default is 9001.

`-s [full chain] [private key]` or `--secure [full chain] [private key]`

Use secure WebSockets.
