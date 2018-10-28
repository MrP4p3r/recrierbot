from recrierbot.__main__ import main


def debuginfo():
    import sys
    import asyncio
    print(sys.version, file=sys.stderr)
    print(dir(asyncio), file=sys.stderr)


if __name__ == '__main__':
    debuginfo()
    main()
