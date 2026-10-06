from archvc.cmds import acc, intx, proxy, router, start, sudo, sys, vc


def wire(app) -> None:
    start.wire(app)
    sudo.wire(app)
    acc.wire(app)
    vc.wire(app)
    intx.wire(app)
    proxy.wire(app)
    sys.wire(app)
    router.wire(app)
