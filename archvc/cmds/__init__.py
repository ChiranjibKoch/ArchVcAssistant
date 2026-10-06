from archvc.cmds import acc, intx, router, start, sudo, sys, vc


def wire(app) -> None:
    start.wire(app)
    sudo.wire(app)
    acc.wire(app)
    vc.wire(app)
    intx.wire(app)
    sys.wire(app)
    router.wire(app)
