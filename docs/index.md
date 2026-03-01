# httpkom

REST-like HTTP API for [LysKOM](https://www.lysator.liu.se/lyskom/).

All content types are `application/json`, unless otherwise specified.

## Connection Model

The httpkom connection id is the unique identifier that a httpkom client uses to identify which LysKOM connection it owns. Since httpkom can be configured to allow connections to several different LysKOM servers, the connection id refers to a specific session on a specific LysKOM server.

The session number is what the LysKOM server uses to identify an open connection.

There is a 1-to-1 relation between httpkom connection ids and LysKOM session numbers. The important difference is that the session number is not secret. Httpkom uses a separate connection identifier — a random UUID — to make it close to impossible to intentionally take over another client's LysKOM connection.

The httpkom connection id is specified as an HTTP header:

```
Httpkom-Connection: <uuid>
```

See [Sessions](sessions.md) for details on how to create a connection and log in.
