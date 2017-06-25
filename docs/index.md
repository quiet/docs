# Quiet Modem Project

Quiet Modem Project is an easy way to provide low-throughput communication for websites and apps without requiring access to Internet or pairing between two devices. It is a set of cross-platform libraries that allow you to encode data as sound and transmit it with a speaker. A device or application with the Quiet Modem can then detect this sound and receive the encoded data. This sound can be audible or nearly ultrasonic. [Forward Error Correction](https://en.wikipedia.org/wiki/Forward_error_correction) applied to the message helps preserve the data against errors in transmission, while [Checksums](https://en.wikipedia.org/wiki/Checksum) discard messages received incorrectly.

## Live Demo
---


All of the Quiet Modem's libraries, and its dependencies, are licensed under a mix of BSD and MIT, allowing a versatile range of use cases. Quiet's source is freely available and can be audited, which ensures that your user's microphone data is safe. Quiet Modem is offered in [C](https://github.com/quiet/quiet), [Javascript](https://github.com/quiet/quiet-js), [Android](https://github.com/quiet/org.quietmodem.Quiet) and [iOS](https://github.com/quiet/QuietModemKit). It provides bindings to soundcards on each platform so that you can simply encode data on one side and decode on the other.

The Quiet Modem is configured with a JSON-based profile system that allows you to change a wide range of behaviors at runtime. Quiet is built on top of a [highly capable DSP/SDR library](http://liquidsdr.org/) which provides it with good robustness, even at distances up to 1 meter.
