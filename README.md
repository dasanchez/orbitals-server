# orbitals-server

This is the WebSockets server for the Orbitals game.

Try a live demo at [urra.ca](https://urra.ca/orbitals/)!

## Dependencies

The server is built with Python 3.6 and the [websockets](https://websockets.readthedocs.io/en/stable/) library.

## Usage

In order to start the server, run:

```
python or_server.py
```

### Options

`-p [x]`  
`--port [x]`

Listen on port x. Default is 9001.

`-s [full chain] [private key]`  
`--secure [full chain] [private key]`

Use secure WebSockets.
