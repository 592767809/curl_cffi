import json
import base64
from io import BytesIO
import pytest

from curl_cffi import Curl, CurlInfo, CurlOpt, CurlError


#######################################################################################
# testing setopt
#######################################################################################


def test_get(server):
    c = Curl()
    c.setopt(CurlOpt.URL, str(server.url).encode())
    c.perform()


def test_post(server):
    c = Curl()
    url = str(server.url.copy_with(path="/echo_body"))
    c.setopt(CurlOpt.URL, url.encode())
    c.setopt(CurlOpt.POST, 1)
    c.setopt(CurlOpt.POSTFIELDS, b"foo=bar")
    buffer = BytesIO()
    c.setopt(CurlOpt.WRITEFUNCTION, buffer.write)
    c.perform()
    assert buffer.getvalue() == b"foo=bar"


def test_put(server):
    c = Curl()
    c.setopt(CurlOpt.URL, str(server.url).encode())
    c.setopt(CurlOpt.CUSTOMREQUEST, b"PUT")
    c.perform()


def test_delete(server):
    c = Curl()
    c.setopt(CurlOpt.URL, str(server.url).encode())
    c.setopt(CurlOpt.CUSTOMREQUEST, b"DELETE")
    c.perform()


def test_post_data_with_size(server):
    c = Curl()
    url = str(server.url.copy_with(path="/echo_body"))
    c.setopt(CurlOpt.URL, url.encode())
    c.setopt(CurlOpt.CUSTOMREQUEST, b"POST")
    c.setopt(CurlOpt.POSTFIELDS, b"\0" * 7)
    c.setopt(CurlOpt.POSTFIELDSIZE, 7)
    buffer = BytesIO()
    c.setopt(CurlOpt.WRITEFUNCTION, buffer.write)
    c.perform()
    assert buffer.getvalue() == b"\0" * 7


def test_headers(server):
    c = Curl()
    url = str(server.url.copy_with(path="/echo_headers"))
    c.setopt(CurlOpt.URL, url.encode())
    c.setopt(CurlOpt.HTTPHEADER, [b"Foo: bar"])
    buffer = BytesIO()
    c.setopt(CurlOpt.WRITEFUNCTION, buffer.write)
    c.perform()
    headers = json.loads(buffer.getvalue().decode())
    assert headers["Foo"] == "bar"


def test_cookies(server):
    c = Curl()
    url = str(server.url.copy_with(path="/echo_cookies"))
    c.setopt(CurlOpt.URL, url.encode())
    c.setopt(CurlOpt.COOKIE, b"foo=bar")
    buffer = BytesIO()
    c.setopt(CurlOpt.WRITEFUNCTION, buffer.write)
    c.perform()
    cookies = json.loads(buffer.getvalue().decode())
    print(cookies)
    assert cookies["foo"] == "bar"


def test_auth(server):
    c = Curl()
    url = str(server.url.copy_with(path="/echo_headers"))
    c.setopt(CurlOpt.URL, url.encode())
    c.setopt(CurlOpt.USERNAME, b"foo")
    c.setopt(CurlOpt.PASSWORD, b"bar")
    buffer = BytesIO()
    c.setopt(CurlOpt.WRITEFUNCTION, buffer.write)
    c.perform()
    headers = json.loads(buffer.getvalue().decode())
    assert headers["Authorization"] == f"Basic {base64.b64encode(b'foo:bar').decode()}"


def test_timeout(server):
    c = Curl()
    url = str(server.url.copy_with(path="/slow_response"))
    c.setopt(CurlOpt.URL, url.encode())
    c.setopt(CurlOpt.TIMEOUT_MS, 100)
    with pytest.raises(CurlError, match=r'ErrCode: 28'):
        c.perform()


def test_follow_redirect(server):
    c = Curl()
    url = str(server.url.copy_with(path="/redirect_301"))
    c.setopt(CurlOpt.URL, url.encode())
    c.setopt(CurlOpt.FOLLOWLOCATION, 1)
    c.perform()
    assert c.getinfo(CurlInfo.RESPONSE_CODE) == 200


def test_not_follow_redirect(server):
    c = Curl()
    url = str(server.url.copy_with(path="/redirect_301"))
    c.setopt(CurlOpt.URL, url.encode())
    c.perform()
    assert c.getinfo(CurlInfo.RESPONSE_CODE) == 301


def test_http_proxy_changed_path(server):
    c = Curl()
    proxy_url = str(server.url)
    c.setopt(CurlOpt.URL, b"http://example.org")
    c.setopt(CurlOpt.PROXY, proxy_url.encode())
    buffer = BytesIO()
    c.setopt(CurlOpt.WRITEFUNCTION, buffer.write)
    c.perform()
    rsp = json.loads(buffer.getvalue().decode())
    assert rsp["Hello"] == "http_proxy!"


def test_https_proxy_using_connect(server):
    c = Curl()
    proxy_url = str(server.url)
    c.setopt(CurlOpt.URL, b"https://example.org")
    c.setopt(CurlOpt.PROXY, proxy_url.encode())
    c.setopt(CurlOpt.HTTPPROXYTUNNEL, 1)
    buffer = BytesIO()
    c.setopt(CurlOpt.WRITEFUNCTION, buffer.write)
    with pytest.raises(CurlError, match=r'ErrCode: 35'):
        c.perform()


def test_verify(https_server):
    c = Curl()
    url = str(https_server.url)
    c.setopt(CurlOpt.URL, url.encode())
    with pytest.raises(CurlError, match="SSL certificate problem"):
        c.perform()


def test_verify_false(https_server):
    c = Curl()
    url = str(https_server.url)
    c.setopt(CurlOpt.URL, url.encode())
    c.setopt(CurlOpt.SSL_VERIFYPEER, 0)
    c.setopt(CurlOpt.SSL_VERIFYHOST, 0)
    c.perform()


def test_referer(server):
    c = Curl()
    url = str(server.url.copy_with(path="/echo_headers"))
    c.setopt(CurlOpt.URL, url.encode())
    c.setopt(CurlOpt.REFERER, b"http://example.org")
    buffer = BytesIO()
    c.setopt(CurlOpt.WRITEFUNCTION, buffer.write)
    c.perform()
    headers = json.loads(buffer.getvalue().decode())
    assert headers["Referer"] == "http://example.org"


#######################################################################################
# testing getinfo
#######################################################################################


def test_effective_url(server):
    c = Curl()
    url = str(server.url.copy_with(path="/redirect_301"))
    c.setopt(CurlOpt.URL, url.encode())
    c.setopt(CurlOpt.FOLLOWLOCATION, 1)
    c.perform()
    assert c.getinfo(CurlInfo.EFFECTIVE_URL) == str(server.url).encode()


def test_status_code(server):
    c = Curl()
    url = str(server.url)
    c.setopt(CurlOpt.URL, url.encode())
    c.perform()
    assert c.getinfo(CurlInfo.RESPONSE_CODE) == 200


def test_response_headers(server):
    c = Curl()
    url = str(server.url.copy_with(path="/set_headers"))
    c.setopt(CurlOpt.URL, url.encode())
    buffer = BytesIO()
    c.setopt(CurlOpt.HEADERDATA, buffer)
    c.perform()
    headers = buffer.getvalue().decode()
    for line in headers.splitlines():
        if line.startswith("x-test"):
            assert line.startswith("x-test: test")


def test_response_cookies(server):
    c = Curl()
    url = str(server.url.copy_with(path="/set_cookies"))
    c.setopt(CurlOpt.URL, url.encode())
    buffer = BytesIO()
    c.setopt(CurlOpt.HEADERDATA, buffer)
    c.perform()
    headers = buffer.getvalue()
    cookie = c.parse_cookie_headers(headers.splitlines())
    for name, morsel in cookie.items():
        if name == "foo":
            assert morsel.value == "bar"


def test_elapsed(server):
    c = Curl()
    url = str(server.url)
    c.setopt(CurlOpt.URL, url.encode())
    c.perform()
    assert c.getinfo(CurlInfo.TOTAL_TIME) > 0


def test_reason(server):
    c = Curl()
    url = str(server.url)
    c.setopt(CurlOpt.URL, url.encode())
    buffer = BytesIO()
    c.setopt(CurlOpt.HEADERDATA, buffer)
    c.perform()
    headers = buffer.getvalue()
    headers = headers.splitlines()
    assert c.get_reason_phrase(headers[0]) == b"OK"