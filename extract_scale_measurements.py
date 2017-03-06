#!/usr/bin/python3
"""Example of using hangups.build_user_conversation_list to data."""
import os
import argparse
import asyncio
import gspread
import logging
from dateutil.parser import parse
from oauth2client.service_account import ServiceAccountCredentials
from collections import namedtuple

import hangups
import appdirs

ScaleEntry = namedtuple('ScaleEntry', ['timestamp', 'weight', 'fat', 'water', 'muscle', 'bone'])


def insert_entries_into_spreadsheet(new_entries):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        '/home/ddboline/setup_files/build/gapi_scripts/gspread.json',
        ['https://spreadsheets.google.com/feeds'])
    gc = gspread.authorize(credentials)

    spreadsheet = gc.open('Scale Measurement (Responses)')
    wsheet = spreadsheet.sheet1

    current_entries = {}
    csv = map(lambda x: x.split(','), wsheet.export().decode().split('\r\n'))

    for irow, vals in enumerate(csv):
        if irow == 0:
            continue
        tstamp = parse(vals[0])
        weight, fat, water, muscle, bone = [float(x) for x in vals[1:]]
        entry = ScaleEntry(tstamp, weight, fat, water, muscle, bone)
        current_entries[tstamp.date().isoformat()] = entry
        last_row = irow

    current_days = set(current_entries.keys())
    new_days = set(new_entries.keys()) - current_days

    for day in sorted(new_days):
        new_entry = new_entries[day]
        wsheet.insert_row([getattr(new_entry, x) for x in new_entry._fields], index=last_row)
        print(new_entries[day])
        current_entries[day] = new_entry
    return current_entries


@asyncio.coroutine
def extract_scale_inputs(client, _):
    user_list, conversation_list = (yield from hangups.build_user_conversation_list(client))
    all_conversations = conversation_list.get_all(include_archived=True)

    print('{} known conversations'.format(len(all_conversations)))
    entries = set()
    for conversation in all_conversations:
        if all(x.full_name == 'Daniel Boline' for x in conversation.users):
            oldest_event = None
            oldest_time = None
            for event in conversation.events:
                if oldest_time is None or event.timestamp < oldest_time:
                    oldest_event = event.id_
                    oldest_time = event.timestamp
            for _ in range(10):
                conversation.get_events(event_id=oldest_event)
                for event in conversation.events:
                    if event.timestamp < oldest_time:
                        oldest_event = event.id_
                        oldest_time = event.timestamp
                    if event.text[0].isnumeric():
                        entries.add((event.text.strip(), event.timestamp.isoformat()))
    new_entries = {}
    for txt, tstmp in entries:
        tstmp = parse(tstmp)
        weight, fat, water, muscle, bone = [int(x) / 10. for x in txt.split(':')]
        new_entry = ScaleEntry(tstmp, weight, fat, water, muscle, bone)
        new_entries[tstmp.date().isoformat()] = new_entry
    insert_entries_into_spreadsheet(new_entries)


def run_example(example_coroutine, *extra_args):
    """Run a hangups example coroutine.

    Args:
        example_coroutine (coroutine): Coroutine to run with a connected
            hangups client and arguments namespace as arguments.
        extra_args (str): Any extra command line arguments required by the
            example.
    """
    args = _get_parser(extra_args).parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARNING)
    # Obtain hangups authentication cookies, prompting for credentials from
    # standard input if necessary.
    cookies = hangups.auth.get_auth_stdin(args.token_path)
    client = hangups.Client(cookies)
    task = asyncio.async(_async_main(example_coroutine, client, args))
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        task.cancel()
        loop.run_forever()
    finally:
        loop.close()


def _get_parser(extra_args):
    """Return ArgumentParser with any extra arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, )
    dirs = appdirs.AppDirs('hangups', 'hangups')
    default_token_path = os.path.join(dirs.user_cache_dir, 'refresh_token.txt')
    parser.add_argument(
        '--token-path', default=default_token_path, help='path used to store OAuth refresh token')
    parser.add_argument(
        '-d', '--debug', action='store_true', help='log detailed debugging messages')
    for extra_arg in extra_args:
        parser.add_argument(extra_arg, required=True)
    return parser


@asyncio.coroutine
def _async_main(example_coroutine, client, args):
    """Run the example coroutine."""
    # Spawn a task for hangups to run in parallel with the example coroutine.
    task = asyncio.async(client.connect())

    # Wait for hangups to either finish connecting or raise an exception.
    on_connect = asyncio.Future()
    client.on_connect.add_observer(lambda: on_connect.set_result(None))
    done, _ = yield from asyncio.wait((on_connect, task), return_when=asyncio.FIRST_COMPLETED)
    yield from asyncio.gather(*done)

    # Run the example coroutine. Afterwards, disconnect hangups gracefully and
    # yield the hangups task to handle any exceptions.
    try:
        yield from example_coroutine(client, args)
    finally:
        yield from client.disconnect()
        yield from task


if __name__ == '__main__':
    run_example(extract_scale_inputs)
