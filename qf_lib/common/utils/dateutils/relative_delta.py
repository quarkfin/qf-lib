from dateutil.relativedelta import relativedelta


class RelativeDelta(relativedelta):
    def __eq__(self, other):
        if other is self:
            return True

        if not isinstance(other, RelativeDelta):
            return False

        return (self.years, self.months, self.days, self.leapdays, self.hours, self.minutes, self.seconds,
                self.microseconds, self.year, self.month, self.day, self.weekday, self.hour, self.minute,
                self.second, self.microsecond) == \
               (other.years, other.months, other.days, other.leapdays, other.hours, other.minutes, other.seconds,
                other.microseconds, other.year, other.month, other.day, other.weekday, other.hour, other.minute,
                other.second, other.microsecond)

    def __hash__(self):
        return hash((self.years, self.months, self.days, self.leapdays, self.hours, self.minutes, self.seconds,
                     self.microseconds, self.year, self.month, self.day, self.weekday, self.hour, self.minute,
                     self.second, self.microsecond))
