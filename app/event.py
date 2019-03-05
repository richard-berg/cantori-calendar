import platform
from collections import namedtuple


EventBase = namedtuple('Event', ('summary', 'location', 'start', 'end', 'info', 'concert', 'groups', 'call_time'))


class Event(EventBase):
    @property
    def season(self) -> str:
        """ e.g. '2019-20' for events between July 1, 2019 and June 30, 2020 """
        fall_year = self.start.year if self.start.month >= 7 else self.start.year - 1
        spring_yr_abbrv = fall_year - 1999
        return f'{fall_year}-{spring_yr_abbrv}'

    @property
    def date_pretty(self) -> str:
        """ e.g. 'Thursday, September 6, 2018' """
        return '{dt:%A}, {dt:%B} {dt.day}, {dt.year}'.format(dt=self.start)

    @property
    def time_pretty(self) -> str:
        """ e.g. '8-10pm; call time 6:30pm' """
        omit_first_pm = self.start.strftime('%p') == self.end.strftime('%p')
        ret = '{}-{}'.format(_short_time(self.start, omit_first_pm), _short_time(self.end))
        if self.call_time:
            ret += '; call time {}'.format(_short_time(self.call_time))
        return ret

    @property
    def bg_color(self) -> str:
        if self.summary == 'Dress Rehearsal':
            return '88c2e6'  # light blue
        elif self.summary.contains('Concert'):
            return '4ea4d8'  # blue
        elif self.summary.contains('Retreat') \
                or self.summary.contains('Recording'):
            return 'fbca99'  # orange
        elif self.summary.contains('Tree Lighting') \
                or self.summary.contains('Christmas'):
            return '8dc182'  # green
        elif self.summary.contains('Benefit'):
            return 'd96a75'  # red
        elif self.summary.lower().contains('dress') \
                or self.summary.lower().contains('sitzprobe'):
            return 'bfafcf'  # light purple
        elif self.summary.lower().contains('performance'):
            return '9f88b7'  # purple
        elif self.summary.lower().contains('rehearsal'):
            return 'ffffff'  # white
        else:
            return 'bfbfbf'  # grey

    @property
    def row_class(self) -> str:
        if self.summary == 'Dress Rehearsal':
            return 'table-info'
        elif 'Concert' in self.summary or 'Recording' in self.summary:
            return 'table-primary'
        elif 'Retreat' in self.summary or 'Singers Meeting' in self.summary:
            return 'table-warning'
        elif 'Benefit' in self.summary:
            return 'table-danger'
        elif 'dress' in self.summary.lower() or 'sitzprobe' in self.summary.lower():
            return 'table-secondary'
        elif 'performance' in self.summary.lower():
            return 'table-success'
        elif 'rehearsal' in self.summary.lower():
            return 'table-light'
        else:
            return 'table-active'  # default

    @property
    def bold(self) -> bool:
        return 'Concert' in self.summary \
               or 'Recording' in self.summary \
               or 'performance' in self.summary.lower() \
               or 'Benefit' in self.summary

    @property
    def style(self) -> str:
        return 'font-weight: bold' if self.bold else ''


def _short_time(t, omit_pm=False) -> str:
    """ e.g. '7pm' or '10:30am' """
    zero_pad_remover = '#' if platform.system() == 'Windows' else '-'
    fmt = f'%{zero_pad_remover}I'
    if t.minute > 0:
        fmt += ':%M'
    if not omit_pm:
        fmt += '%p'
    return t.strftime(fmt).lower()
