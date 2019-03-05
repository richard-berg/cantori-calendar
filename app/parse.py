import logging
from collections import namedtuple
from datetime import date, datetime
from typing import List

import requests
from dateutil.tz import gettz
from icalendar import Calendar
from sortedcontainers import SortedDict

from app.event import Event

DEFAULT_TIME_ZONE = 'America/New_York'


class AddressBook(SortedDict):
    def enrich(self, short_name, full_location):
        full_address = full_location.replace(short_name + ', ', '')
        if short_name in self and self[short_name] != full_address:
            logging.warning("Will replace '%s' with existing address book entry '%s'",
                            full_address, self[short_name])
        self[short_name] = full_address

    KNOWN_PLACES = frozenset({'Interchurch', 'Ripley Grier', 'St Luke', 'Quantedge', 'Holy Apostle'})

    def shorten_location(self, location):
        # Derive the shorthand alias for a given location, while storing the full location name into the address
        # book (so a glossary can be provided later)
        if ',' not in (location or ''):
            return location
        short_name = location.split(',')[0]
        for kp in self.KNOWN_PLACES:
            if kp in short_name:
                self.enrich(kp, location)
                return kp

        self.enrich(short_name, location)
        return short_name


class ChorusCalendar(object):
    """Immutable representation of a calendar in Chorus Connection.

    The __init__ method should only be called internally.  Outside this module, stick to the factory methods.

    Attributes:
          title (str): Title found in the iCal representation -- should be your CC ensemble name
          as_of (datetime): When the calendar was last updated
          tz (dateutil.zoneinfo.tzfile): TZ in which to render events
          events (:obj:`list` of :obj:`Event`): the actual contents of the calendar
    """
    def __init__(self, title, as_of, tz, events, address_book=AddressBook()):
        self.title = title
        self.as_of = as_of
        self.tz = tz
        self.events = events
        self.address_book = address_book

    def filter_seasons(self, seasons: List[str]):
        events = [e for e in self.events if e.season in seasons]
        return ChorusCalendar(self.title, self.as_of, self.tz, events)

    def filter_groups(self, groups: List[str]):
        events = [e for e in self.events if not e.groups or e.groups.intersection(groups)]
        return ChorusCalendar(self.title, self.as_of, self.tz, events)

    def collapse_call_times(self):
        events = list(_collapse_call_times(self.events))
        return ChorusCalendar(self.title, self.as_of, self.tz, events)

    def shorten_locations(self):
        # noinspection PyProtectedMember
        events = [e._replace(location=self.address_book.shorten_location(e.location)) for e in self.events]
        return ChorusCalendar(self.title, self.as_of, self.tz, events, self.address_book)

    @property
    def seasons(self):
        return set(e.season for e in self.events)

    @property
    def seasons_pretty(self):
        return ', '.join(sorted(self.seasons))

    @property
    def groups(self):
        return set.union(*[e.groups for e in self.events])


def from_webcal(url: str, time_zone: str = DEFAULT_TIME_ZONE) -> ChorusCalendar:
    ical_txt = _fetch_webcal(url)
    parser = IcalParser(time_zone)
    return parser.parse(ical_txt)


def _fetch_webcal(webcal_url):
    url = webcal_url.replace('webcal://', 'https://')
    r = requests.get(url)
    r.raise_for_status()
    return r.text


def _collapse_call_times(events):
    # given an ordered sequence of Event, remove any "call time" events, placing the info in the subsequent
    # "performance" event instead
    CallFor = namedtuple('CallFor', ('summary', 'start'))
    prev_call = None
    for event in events:
        if event.summary.startswith('Call for '):
            prev_call = CallFor(event.summary.replace('Call for ', ''), event.start)
        elif prev_call and prev_call.summary == event.summary:
            # noinspection PyProtectedMember
            yield event._replace(call_time=prev_call.start)
            prev_call = None
        else:
            yield event
            prev_call = None


class IcalParser(object):
    def __init__(self, time_zone=DEFAULT_TIME_ZONE):
        self.tz = gettz(time_zone)

    def parse(self, ical_txt: str) -> ChorusCalendar:
        cal = Calendar.from_ical(ical_txt)
        title = str(cal['X-WR-CALNAME'])
        as_of = cal.subcomponents[0]['DTSTAMP'].dt.astimezone(self.tz)
        events = sorted((self._parse_vevent(ve) for ve in cal.subcomponents),
                        key=lambda e: e.start)
        return ChorusCalendar(title, as_of, self.tz, events)

    def _parse_vevent(self, vevent):
        info, concert, groups = _parse_description(str(vevent.get('DESCRIPTION')))
        return Event(
            summary=str(vevent.get('SUMMARY')),
            location=str(vevent.get('LOCATION')),
            start=self._force_datetime(vevent['DTSTART'].dt),
            end=self._force_datetime(vevent['DTEND'].dt),
            info=info,
            concert=concert,
            groups=groups,
            call_time=None,
        )

    def _force_datetime(self, dt):
        # icalendar sometimes parses DTSTART/END fields into datetimes, sometimes into plain dates
        if isinstance(dt, datetime):
            return dt
        elif isinstance(dt, date):
            midnight = datetime.min.replace(tzinfo=self.tz).timetz()
            return datetime.combine(dt, midnight)
        else:
            raise ValueError(f'Unexpected date type: {dt}')


def _parse_description(description):
    info = concert = ''
    groups = set()
    for line in description.split('\n\n'):
        if line.startswith('Info: '):
            info = line.replace('Info: ', '')
        elif line.startswith('Concert: '):
            concert = line.replace('Concert: ', '')
        elif line.startswith('Group: '):
            groups = set(line.replace('Group: ', '').split(', '))
    return info, concert, groups



