<div align="center">
  <img src="https://raw.githubusercontent.com/Rakagami/rear/main/images/logo.png">
</div>

[![Python](https://img.shields.io/badge/python-3.7.6-blue)]()
[![WIP](https://img.shields.io/badge/version-WIP-red)]()

[RadioEar](https://github.com/Rakagami/rear) - A tool to eavesdrop whatever is currently in the air (radio).

## How it works

<div align="center">
  <img src="https://raw.githubusercontent.com/Rakagami/rear/main/images/diagram.png">
</div>

We use [GQRX](https://gqrx.dk/) and use the UDP output stream to feed it into RadioEar. Internally, RadioEar uses [DeepSpeech](https://github.com/mozilla/DeepSpeech) to perform speech recognition on the audio data. The stream of recognized words are inserted into [Grafana](https://grafana.com/) which is a visualization front-end for data.

## Current State

wip

## Links

- https://deepspeech.readthedocs.io/en/r0.9/
- https://github.com/AASHISHAG/deepspeech-german
