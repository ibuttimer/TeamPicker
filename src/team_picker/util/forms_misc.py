from enum import IntEnum, auto

NO_OPTION_SELECTED = -1

# choices for possible venues
HOME_VENUE = 0
AWAY_VENUE = 1
# choices for possible venues
VENUE_CHOICES = [
    (HOME_VENUE, 'Home'),
    (AWAY_VENUE, 'Away'),
]
# valid options for venue selection
VENUES = [s[0] for s in VENUE_CHOICES]

# choices for possible confirmed status
NO_STATUS = 0
NOT_AVAILABLE_STATUS = 1
MAYBE_STATUS = 2
CONFIRMED_STATUS = 3


class DateRange(IntEnum):
    """ Enum of date ranges """
    IGNORE_DATE = auto()
    BEFORE_DATE = auto()
    BEFORE_OR_EQUAL_DATE = auto()
    EQUAL_DATE = auto()
    AFTER_OR_EQUAL_DATE = auto()
    AFTER_DATE = auto()

    @staticmethod
    def coerce(value):
        """
        Coerce function for forms.
        :param value:
        :return:
        """
        coerced = value
        if isinstance(value, str):
            for val in DateRange:
                if value == f"DateRange.{val.name}":
                    coerced = val
                    break
        return coerced


# valid options for date range selection
DATE_RANGE_CHOICES = [
    (DateRange.IGNORE_DATE, "Don't care"),
    (DateRange.BEFORE_DATE, "Before"),
    (DateRange.BEFORE_OR_EQUAL_DATE, "On or before"),
    (DateRange.EQUAL_DATE, 'On'),
    (DateRange.AFTER_OR_EQUAL_DATE, 'On or after'),
    (DateRange.AFTER_DATE, 'After'),
]
DATE_RANGES = [s[0] for s in DATE_RANGE_CHOICES]


class FormArgs(IntEnum):
    """ Enum of form args """
    CURRENT_MIN = auto()    # Only future date/times allowed
    FREE_MIN = auto()       # Past date/times allowed
    TEAM_REQ = auto()       # Team selection required
    TEAM_NOT_REQ = auto()   # Team selection not required
