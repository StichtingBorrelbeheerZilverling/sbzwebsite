from django.db import models


class FlowValue(models.Model):
    channel = models.ForeignKey("flowguard.FlowChannel", on_delete=models.CASCADE)
    value = models.DecimalField(decimal_places=1, max_digits=10)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()

    def __str__(self):
        return "Value of {} between {} and {}: {}".format(self.channel, self.first_seen, self.last_seen, self.value)


class FlowChannel(models.Model):
    index = models.PositiveIntegerField()
    name = models.CharField(max_length=255)

    def __str__(self):
        return "{} (Index {})".format(self.name, self.index)
