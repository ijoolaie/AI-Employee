"""Minimal deterministic SMTP sink for E2E provider certification only.

It accepts plaintext SMTP on :2525 and appends accepted RFC822 messages to
/smtp-outbox/messages.eml. It is intentionally not a production mail server.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

HOST = "0.0.0.0"
PORT = 2525
OUT = Path("/smtp-outbox/messages.eml")


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    async def send(line: str) -> None:
        writer.write((line + "\r\n").encode())
        await writer.drain()

    await send("220 ai-employee-e2e-smtp ESMTP")
    data_lines: list[str] = []
    in_data = False
    try:
        while True:
            raw = await reader.readline()
            if not raw:
                break
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            upper = line.upper()
            if in_data:
                if line == ".":
                    OUT.parent.mkdir(parents=True, exist_ok=True)
                    with OUT.open("a", encoding="utf-8") as fh:
                        fh.write("\n".join(data_lines))
                        fh.write("\n---END-MESSAGE---\n")
                    data_lines.clear()
                    in_data = False
                    await send("250 2.0.0 accepted")
                else:
                    data_lines.append(line[1:] if line.startswith("..") else line)
                continue
            if upper.startswith("EHLO") or upper.startswith("HELO"):
                await send("250-ai-employee-e2e-smtp")
                await send("250 SIZE 10485760")
            elif upper.startswith("MAIL FROM:") or upper.startswith("RCPT TO:"):
                await send("250 2.0.0 ok")
            elif upper == "DATA":
                in_data = True
                await send("354 End data with <CR><LF>.<CR><LF>")
            elif upper == "RSET":
                data_lines.clear()
                in_data = False
                await send("250 2.0.0 reset")
            elif upper == "NOOP":
                await send("250 2.0.0 ok")
            elif upper == "QUIT":
                await send("221 2.0.0 bye")
                break
            else:
                await send("250 2.0.0 ok")
    finally:
        writer.close()
        await writer.wait_closed()


async def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    server = await asyncio.start_server(handle, HOST, PORT)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
