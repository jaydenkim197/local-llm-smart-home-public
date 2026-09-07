#!/usr/bin/env python3
"""Temporary LAN TCP relay for the HA dashboard, including WebSocket traffic."""

import argparse
import asyncio
import ipaddress
import logging


async def relay(reader, writer, args):
    peer = writer.get_extra_info("peername")
    upstream = None
    tasks = []
    try:
        if not peer or ipaddress.ip_address(peer[0]) not in args.allowed_network:
            return
        remote_reader, upstream = await asyncio.wait_for(
            asyncio.open_connection(args.target, args.target_port), timeout=5
        )
        logging.info("Connection from %s", peer[0])

        async def copy(source, destination):
            while True:
                data = await source.read(65536)
                if not data:
                    if destination.can_write_eof():
                        destination.write_eof()
                    return
                destination.write(data)
                await destination.drain()

        tasks = [asyncio.create_task(copy(reader, upstream)),
                 asyncio.create_task(copy(remote_reader, writer))]
        await asyncio.gather(*tasks)
    except (OSError, asyncio.TimeoutError) as error:
        logging.warning("Connection failed: %s", error)
    finally:
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        for stream in (writer, upstream):
            if stream is not None:
                stream.close()
                try:
                    await stream.wait_closed()
                except OSError:
                    pass


async def main(args):
    server = await asyncio.start_server(
        lambda reader, writer: relay(reader, writer, args), args.bind, args.port
    )
    logging.info("Listening on %s:%s -> %s:%s", args.bind, args.port,
                 args.target, args.target_port)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", required=True)
    parser.add_argument("--port", type=int, default=8123)
    parser.add_argument("--target", required=True)
    parser.add_argument("--target-port", type=int, default=80)
    parser.add_argument("--allowed-network", type=ipaddress.ip_network, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    asyncio.run(main(args))
