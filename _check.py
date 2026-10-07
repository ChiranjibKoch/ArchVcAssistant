try:
    from archvc.cmds import copydb_cmd
    print("copydb_cmd import ok")
    print("has wire:", hasattr(copydb_cmd, "wire"))
except Exception as e:
    import traceback
    traceback.print_exc()

try:
    from archvc.acct import copydb
    print("copydb ok, names:", [m for m in dir(copydb) if not m.startswith("_")])
except Exception as e:
    import traceback
    traceback.print_exc()
