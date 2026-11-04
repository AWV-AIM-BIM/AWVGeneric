from API.clients.fs import FSClient
from UnitTests.helpers.mock_requester import MockRequester, MockResponse


def test_fs_process_chunk():
    class Pbar:
        def update(self, n):
            pass

    result = []
    gen = FSClient._process_chunk('{"a":1}\n{"b":2}\n', Pbar())
    for item in gen:
        result.append(item)
    assert len(result) == 2


def test_fs_download_layer_to_records():
    class R:
        status_code = 200
        content = b"ok"

        def iter_content(self, chunk_size=1024 * 256):
            yield b'{"a":1}\n{"b":2}\n'

    class Req:
        first_part_url = ""
        def get(self, url="", **kwargs):
            return R()

    client = FSClient.__new__(FSClient)
    client.requester = Req()
    records = list(client.download_layer_to_records("test"))
    assert len(records) == 2
