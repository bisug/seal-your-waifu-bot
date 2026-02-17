try:
    import builtins
    builtins.__import__ = __import__ # restore import
    from Grabber.modules import propose
    print("Syntax OK")
except ImportError as e:
    # We expect ImportErrors because dependencies (Grabber.app, etc) are not actually running/available
    # But if we get a SyntaxError, it will be raised before ImportError usually (if in the file itself)
    # Actually, python compiles the file first.
    print(f"ImportError (Expected): {e}")
except SyntaxError as e:
    print(f"SyntaxError: {e}")
except Exception as e:
    print(f"Other Error: {e}")
