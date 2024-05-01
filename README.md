# qubes-color
Colorify text in Qubes' global clipboard

#### Setup

Before using this script, you need to create a named disposable `sys-colorify`, which will do the actual processing. This way, dom0 is entirely isolated from any potentially-malicious inputs

`sys-colorify` can be based on any template, including minimal templates. It is recommended to deny network access, since it really has no need to connect to the internet

### How to copy files to dom0

The Qubes official documentation has information about copying files to dom0: https://www.qubes-os.org/doc/how-to-copy-from-dom0/#copying-to-dom0

For the best security, you should download this into a disposable VM, to prevent a compromised qube from tampering with the data locally
