# qubes-color
Colorify text in Qubes' global clipboard

#### Warning:

This script parses the Qubes global clipboard (which is encoded via UTF-8). It's possible for the Python environment to be buggy, and as a result, the security of dom0 cannot be completely guaranteed when using this script, if the clipboard is maliciously modified

The script is a very small security risk, but this doesn't mean it's not a risk. There's a non-zero chance that it gets exploited to compromise dom0

You've been warned

### How to copy files to dom0

The Qubes official documentation has information about copying files to dom0: https://www.qubes-os.org/doc/how-to-copy-from-dom0/#copying-to-dom0

For the best security, you should download this into a disposable VM, to prevent a compromised qube from tampering with the data locally
