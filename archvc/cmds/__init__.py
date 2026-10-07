import traceback

from archvc.cmds import (
    acc,
    approve_cmd,
    autoview_cmd,
    copydb_cmd,
    help_cmd,
    intx,
    proxy,
    rejoin,
    router,
    start,
    sudo,
    sys,
    vc,
    vcreact_cmd,
    watch_cmd,
    wipe_cmd,
)

_MODULES = [
    start, sudo, acc, vc, intx, proxy, sys, router,
    vcreact_cmd, rejoin, autoview_cmd, approve_cmd, copydb_cmd, wipe_cmd,
    help_cmd,
]


def wire(app) -> None:
    ok = []
    fail = []
    for mod in _MODULES:
        try:
            mod.wire(app)
            ok.append(mod.__name__)
            print(f"[wire] ok: {mod.__name__}", flush=True)
        except Exception as e:
            fail.append(mod.__name__)
            print(f"[wire] FAIL: {mod.__name__}: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc()
    print(f"[wire] total ok={len(ok)} fail={len(fail)}", flush=True)
    if fail:
        print(f"[wire] failed modules: {fail}", flush=True)
