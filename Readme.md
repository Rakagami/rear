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

## How to use

1. Download the DeepSpeech weights, a `.pbmm` file and a `.scorer` file. (Model names are still hardcoded)

2. Start the tool with `docker compose up`

3. Initialize the mysql database with the script `debugtools/mysqltest.py` (this is very hacky)

4. Set up a Grafana dashboard with the correct mysql data source (I don't know yet how to make Grafana settings persistent with docker)

5. Start up a GQRXX instance on your computer and stream the output to localhost on port 7355

6. And now you're done! Enjoy watching the word stream on the Grafana instance :D

## Current State

wip

## Links

- https://deepspeech.readthedocs.io/en/r0.9/
- https://github.com/AASHISHAG/deepspeech-german
