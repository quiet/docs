# Getting Started

## Installing tools

libquiet requires [Cmake](https://cmake.org/) for its builds.

## Installing Dependencies

* Install [libcorrect](https://github.com/quiet/libcorrect)

* Install [liquid dsp](https://github.com/quiet/liquid-dsp/tree/devel). The `devel` branch *must* be installed.

* Install [libjansson](http://www.digip.org/jansson/)

* (Optional) Install [PortAudio](http://www.portaudio.com/) which allows Quiet to interface with your soundcard. This is highly recommended.

* (Optional) Install [libsndfile](http://www.mega-nerd.com/libsndfile/) which allows Quiet to read and write .wav files containing encoded sounds.

## Installing libquiet

After installing all dependencies, clone [libquiet](https://github.com/quiet/quiet), cd to directory where it is cloned, then run
```
mkdir build
cd build
cmake ..
make
make install

```

## Headers

To access libquiet's API,

```
#include &lt;quiet.h&gt;
```

If you have installed PortAudio and have installed libquiet's PortAudio wrapper, you can access the PortAudio-backed transmitter and receiver with

```
#include &lt;quiet-portaudio.h&gt;
```

## Linking
