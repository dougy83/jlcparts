# debug_buildtables.py
from jlcparts.ui import buildtables

# call Click function but don't let it capture/exit
buildtables(
    ["cache.sqlite3", "web/public/data", "--ignoreoldstock", "30"],
    standalone_mode=False
)