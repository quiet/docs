# Profiles

Profiles are the configuration system of Quiet Modem. A single profile sets all of the parameters for both the transmitter and the receiver. Quiet uses a JSON-based serialization for profiles, and any given profile works across all Quiet platforms.

Quiet comes with some starter profiles. These can be used out of the box with good success in a variety of use cases. They will also make a good starting point for more tuning and testing, should you decide to tweak Quiet to fit your use case specifically.

## Structure

Profiles are stored in a file called `quiet-profiles.json`. Inside this file is a single JSON object. The top-level keys of this object are names of profiles, e.g. `ultrasonic-whisper`. The corresponding value for this key contains another object which provides a complete profile for Quiet's transmitter and receiver.

## Quiet Profile Lab

The [Quiet Profile Lab](https://quiet.github.io/quiet-profile-lab) is an interactive testbench that runs in your browser. This allows you to test out new profiles with the speakers and mic in your computer. The Lab has instrumentation that can help you understand how various options change Quiet's behavior.

## mod_scheme

This sets the payload modulation mode for Quiet. Most methods come in a variety of bit depths.

### Gaussian Minimum Shift Keying <sub>[wikipedia](https://en.wikipedia.org/wiki/Minimum-shift_keying#Gaussian_minimum-shift_keying)</sub>

### Phase Shift Keying <sub>[wikipedia](https://en.wikipedia.org/wiki/Phase-shift_keying)

This method can be pictured as a unit circle in the complex plane. Each bit representation contains the same magnitude and varies only in phase on this unit circle.

Comes in `psk2`, `psk4`, `psk8`, `psk16`, `psk32`, `psk64`, `psk128`, `psk256` variants.

### Differential Phase Shift Keying <sub>[wikipedia](https://en.wikipedia.org/wiki/Phase-shift_keying#Differential_phase-shift_keying_.28DPSK.29)

### Amplitude Shift Keying <sub>[wikipedia](https://en.wikipedia.org/wiki/Amplitude-shift_keying)

### Amplitude Phase Shift Keying <sub>[wikipedia](https://en.wikipedia.org/wiki/Amplitude_and_phase-shift_keying)

### Quadrature Amplitude Shift Keying <sub>[wikipedia](https://en.wikipedia.org/wiki/Quadrature_amplitude_modulation)

### Optimal QASK

### Miscellaneous

## ofdm

## ofdm.num_subcarriers

## ofdm.cyclic_prefx_length

## ofdm.taper_length

## ofdm.left_band

## ofdm.right_band

## checksum_scheme

## inner_fec_scheme

## outer_fec_scheme

## frame_length

## modulation

## modulation.center_frequency

## modulation.gain

## interpolation

### interpolation.shape

#### rrcos

## interpolation.samples_per_symbol

## interpolation.symbol_delay

## interpolation.excess_bandwidth

## encoder_filters

## encoder_filters.dc_filter_alpha

## resampler

## resampler.delay

## resampler.bandwidth

## resampler.attenuation

## resampler.filter_bank_size
