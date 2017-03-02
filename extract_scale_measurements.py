"""Example of using hangups.build_user_conversation_list to data."""
import os
import sys
import asyncio
import datetime
import gspread
from dateutil.parser import parse
from oauth2client.service_account import ServiceAccountCredentials
from collections import namedtuple

import hangups

from hangups_common import run_example

ScaleEntry = namedtuple('ScaleEntry', ['timestamp', 'weight', 'fat', 'water', 'muscle', 'bone'])


def insert_entries_into_spreadsheet(new_entries):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        '/home/ddboline/setup_files/build/gapi_scripts/gspread.json', ['https://spreadsheets.google.com/feeds'])
    gc = gspread.authorize(credentials)
    
    spreadsheet = gc.open('Scale Measurement (Responses)')
    wsheet = spreadsheet.sheet1
    
    current_entries = {}
    for irow in range(2, wsheet.row_count):
        if not wsheet.cell(irow, 1).value:
            break
        vals = [x for x in wsheet.row_values(irow) if x]
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


@asyncio.coroutine
def extract_scale_inputs(client, _):
    user_list, conversation_list = (
        yield from hangups.build_user_conversation_list(client)
    )
    all_users = user_list.get_all()
    all_conversations = conversation_list.get_all(include_archived=True)

    #print('{} known users'.format(len(all_users)))
    #for user in all_users:
        #print('    {}: {}'.format(user.full_name, user.id_.gaia_id))

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


if __name__ == '__main__':
    run_example(extract_scale_inputs)
