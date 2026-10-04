from archvc.cmds import acc, intx, router, sudo, sys, vc


def wire(app) -> None:
    sudo.wire(app)
    acc.wire(app)
    vc.wire(app)
    intx.wire(app)
    sys.wire(app)
    router.wire(app)
