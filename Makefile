ninfo-client.pex: setup.py
	pex --python-shebang='/usr/bin/env python' -o ninfo-client.pex . -c ninfo-client
