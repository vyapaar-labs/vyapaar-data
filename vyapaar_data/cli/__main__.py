"""Default entrypoint for `python -m vyapaar_data.cli`."""

import sys

from vyapaar_data.cli.coverage import main

if __name__ == "__main__":
    sys.exit(main())
