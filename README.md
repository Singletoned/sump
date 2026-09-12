# Sump

Sump records Sentry SDK errors in a machine-local registry for coding agents to collect during local development.

The package is under active development and does not yet provide its capture and collection workflow.

## Compatibility

Sump supports Python 3.10 or newer and `sentry-sdk>=2.0.0,<3`. Its custom transport contract is tested against Sentry SDK 2.0.0 and the current version locked by this project.

A custom transport receives envelopes without a DSN, so Sump does not need to configure a remote endpoint. Exceptions raised by synchronous custom transport writes propagate from Sentry capture calls on the tested SDK versions; Sump relies on this behavior to report local storage failures instead of silently losing events.
