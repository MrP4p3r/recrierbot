from aiohttp.web import Request, Response


class StatusHandler(object):

    async def __call__(self, request: Request):
        return Response(status=200, content_type='text/plain', text='Server is ok.')
