from datetime import datetime

from wtforms import ValidationError


class ValidateDateTime(object):
    """
    Validate a date time field
    :param min_dt:     min datetime allowed, or a value of FIELD_DEFAULT uses
                       the field default value
    :param max_dt:     max datetime allowed, or a value of FIELD_DEFAULT uses
                       the field default value
    :param dt_format:  datetime format for error message
    :param message:    validation error message
    """
    FIELD_DEFAULT = 'default'

    def __init__(self, min_dt=datetime.min, max_dt=datetime.max,
                 dt_format=None, message=None):
        self.min = min_dt
        self.max = max_dt
        self.format = dt_format
        self.message = message

    def __call__(self, form, field):
        if self.min == ValidateDateTime.FIELD_DEFAULT:
            min_time = field.default
        else:
            min_time = self.min
        if self.max == ValidateDateTime.FIELD_DEFAULT:
            max_time = field.default
        else:
            max_time = self.max

        min_ng = field.data < min_time
        max_ng = field.data > max_time
        if min_ng or max_ng:
            if self.format is None:
                min_time_str = str(min_time)
                max_time_str = str(max_time)
            else:
                min_time_str = min_time.strftime(self.format)
                max_time_str = max_time.strftime(self.format)

            if self.message is None:
                criteria = f'between {min_time_str} and {max_time_str}'
                if min_ng:
                    if max_time == datetime.max:
                        criteria = f'greater than {min_time_str}'
                else:
                    if min_time == datetime.min:
                        criteria = f'less than {max_time_str}'
                message = f'Invalid datetime, must be {criteria}'
            else:
                message = self.message
            raise ValidationError(message)
