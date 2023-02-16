import json
import shutil

from blight.actions import Demo
from blight.tool import CC


def test_demo(capfd):
    demo = Demo({})

    demo.before_run(CC(["-fake", "-flags"]))
    demo.after_run(CC(["-fake", "-flags"]), run_skipped=False)

    out, err = capfd.readouterr()
    assert "before-run" in err
    assert "after-run" in err
