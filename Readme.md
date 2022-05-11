<div align="center">
  <img src="https://raw.githubusercontent.com/Rakagami/rear/main/images/logo.png">
</div>

[![Python](https://img.shields.io/badge/python-3.7.6-blue)]()

[RadioEar](https://github.com/Rakagami/rear) - A tool to eavesdrop whatever is currently in the air (radio).

## How it works

We use [GQRX](https://gqrx.dk/) and use the UDP output stream to feed it into RadioEar. Internally, RadioEar uses [DeepSpeech](https://github.com/mozilla/DeepSpeech) to perform speech recognition on the audio data. RadioEar itself is a front-end to display the recognized speech data.
