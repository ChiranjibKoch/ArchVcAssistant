from archvc.cmds import (
    acc,
    autoview_cmd,
    intx,
    proxy,
    rejoin,
    router,
    start,
    sudo,
    sys,
    vc,
    vcreact_cmd,
)


def wire(app) -> None:
    start.wire(app)
    sudo.wire(app)
    acc.wire(app)
    vc.wire(app)
    intx.wire(app)
    proxy.wire(app)
    sys.wire(app)
    router.wire(app)
    vcreact_cmd.wire(app)
    rejoin.wire(app)
    autoview_cmd.wire(app)
