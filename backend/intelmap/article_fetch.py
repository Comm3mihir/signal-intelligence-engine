"""Fetch public HTTPS articles without allowing requests into private networks."""

from contextlib import suppress
from threading import Timer
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from html.parser import HTMLParser
import http.client
import ipaddress
import re
import socket
import ssl
import time
from urllib.parse import urljoin, urlsplit


MAX_BYTES = 750_000
MAX_ARTICLE_CHARS = 8_000
TOTAL_TIMEOUT = 12
DNS = ThreadPoolExecutor(max_workers=3, thread_name_prefix="article-dns")
TLS = ssl.create_default_context()


class ArticleUnavailable(ValueError):
    pass


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.publisher = ""
        self.published = ""
        self.paragraphs = []
        self.article_paragraphs = []
        self.in_title = False
        self.in_paragraph = False
        self.in_article = 0
        self.ignored = []
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "nav", "footer", "aside", "noscript", "svg", "template"}:
            self.ignored.append(tag)
        if self.ignored:
            return
        if tag in {"article", "main"}:
            self.in_article += 1
        if tag == "title":
            self.in_title = True
        if tag == "p":
            self.end_paragraph()
            self.in_paragraph = True
        if tag == "meta":
            fields = dict(attrs)
            key = fields.get("property") or fields.get("name")
            value = fields.get("content") or ""
            if key == "og:title":
                self.title = value
            elif key == "og:site_name":
                self.publisher = value
            elif key in {"article:published_time", "datePublished"}:
                self.published = value

    def handle_endtag(self, tag):
        if self.ignored:
            if tag == self.ignored[-1]:
                self.ignored.pop()
            return
        if tag == "title":
            self.in_title = False
        if tag == "p":
            self.end_paragraph()
        if tag in {"article", "main"}:
            self.end_paragraph()
            self.in_article = max(0, self.in_article - 1)

    def handle_data(self, value):
        if self.ignored:
            return
        if self.in_title and not self.title:
            self.title = value
        if self.in_paragraph:
            self.buffer.append(value)

    def end_paragraph(self):
        paragraph = " ".join("".join(self.buffer).split())
        if len(paragraph) >= 45:
            self.paragraphs.append(paragraph)
            if self.in_article:
                self.article_paragraphs.append(paragraph)
        self.in_paragraph = False
        self.buffer.clear()


def public_address(host: str, timeout: float) -> str:
    future = DNS.submit(socket.getaddrinfo, host, 443, 0, socket.SOCK_STREAM)
    try:
        results = future.result(timeout=timeout)
    except (socket.gaierror, FutureTimeout) as exc:
        future.cancel()
        raise ArticleUnavailable("The article’s domain could not be resolved.") from exc
    addresses = list(dict.fromkeys(row[4][0] for row in results))
    if not addresses:
        raise ArticleUnavailable("The article’s domain has no public address.")
    for address in addresses:
        parsed = ipaddress.ip_address(address)
        effective = getattr(parsed, "ipv4_mapped", None) or parsed
        if (not effective.is_global or effective.is_multicast or effective.is_reserved
                or effective.is_loopback or effective.is_link_local or getattr(parsed, "scope_id", None)
                or getattr(parsed, "sixtofour", None) or getattr(parsed, "teredo", None)
                or (parsed.version == 6 and parsed in ipaddress.ip_network("64:ff9b::/96"))):
            raise ArticleUnavailable("Article URLs must resolve exclusively to public addresses.")
    return next((address for address in addresses if ":" not in address), addresses[0])


def parse_url(url: str):
    if len(url) > 2048 or re.search(r"[\x00-\x20\x7f\\]", url):
        raise ArticleUnavailable("The article URL is invalid.")
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").encode("idna").decode()
        valid = (parts.scheme == "https" and parts.port in {None, 443}
                 and parts.username is None and parts.password is None
                 and re.fullmatch(r"[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+", host))
        if not valid or host.lower().endswith((".localhost", ".local", ".internal", ".onion")):
            raise ValueError
        return parts, host
    except (ValueError, UnicodeError) as exc:
        raise ArticleUnavailable("Use a public HTTPS article URL without credentials or a custom port.") from exc


def retrieve(url: str) -> dict:
    deadline = time.monotonic() + TOTAL_TIMEOUT
    visited = set()
    for _ in range(4):
        parts, host = parse_url(url)
        canonical = parts._replace(netloc=host.lower(), fragment="").geturl()
        if canonical in visited or deadline <= time.monotonic():
            raise ArticleUnavailable("The article exceeded the redirect or time limit.")
        visited.add(canonical)
        ip = public_address(host, min(3, deadline - time.monotonic()))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ArticleUnavailable("Article retrieval timed out.")
        connection = http.client.HTTPSConnection(host, timeout=min(4, remaining), context=TLS)
        # TLS checks the URL hostname. The socket connects to the validated literal IP.
        connection._create_connection = lambda _address, timeout, source_address: socket.create_connection(
            (ip, 443), timeout, source_address
        )
        timer = None
        try:
            connection.connect()
            sock = connection.sock
            def interrupt():
                with suppress(OSError):
                    sock.shutdown(socket.SHUT_RDWR)
            timer = Timer(max(0, deadline - time.monotonic()), interrupt)
            timer.daemon = True
            timer.start()
            path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
            connection.request("GET", path, headers={"Accept": "text/html", "Accept-Encoding": "identity",
                                                      "User-Agent": "SIGNAL/1.0 article retrieval"})
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                if not location:
                    raise ArticleUnavailable("The publisher returned an invalid redirect.")
                url = urljoin(canonical, location)
                continue
            if response.status != 200:
                raise ArticleUnavailable(f"The publisher returned HTTP {response.status}.")
            media = (response.getheader("Content-Type") or "").lower().split(";")[0].strip()
            if media not in {"text/html", "application/xhtml+xml"}:
                raise ArticleUnavailable("The URL did not return an HTML article.")
            if (response.getheader("Content-Encoding") or "identity").lower() != "identity":
                raise ArticleUnavailable("The publisher returned an unsupported encoding.")
            length = response.getheader("Content-Length")
            if length and (not length.isdecimal() or int(length) > MAX_BYTES):
                raise ArticleUnavailable("The article response exceeds the download limit.")
            body = bytearray()
            while len(body) <= MAX_BYTES:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ArticleUnavailable("Article retrieval timed out.")
                if connection.sock:
                    connection.sock.settimeout(min(4, remaining))
                chunk = response.read1(min(16_384, MAX_BYTES + 1 - len(body)))
                if not chunk:
                    break
                body.extend(chunk)
            if len(body) > MAX_BYTES:
                raise ArticleUnavailable("The article response exceeds the download limit.")
            parser = ArticleParser()
            parser.feed(body.decode("utf-8", errors="replace"))
            parser.close()
            parser.end_paragraph()
            text = "\n\n".join(parser.article_paragraphs or parser.paragraphs)[:MAX_ARTICLE_CHARS]
            title = " ".join(parser.title.split())[:350]
            if len(text) < 180 or not title:
                raise ArticleUnavailable("No readable article was found. Use a different URL or a manual description.")
            return {"title": title, "publisher": parser.publisher[:120] or host,
                    "published": parser.published, "content": text, "url": canonical}
        except (OSError, http.client.HTTPException, UnicodeError) as exc:
            raise ArticleUnavailable("The article could not be retrieved securely.") from exc
        finally:
            if timer:
                timer.cancel()
            connection.close()
    raise ArticleUnavailable("The article redirected too many times.")
