from django import template

register = template.Library()


@register.filter
def flow_color(value):
    if value == 0.0:
        return "rgb(255, 255, 255)"
    elif value > 0.0:
        max_light = 196
        light = int(max_light - min(max_light, value / 30.0 * max_light))
        return "rgb({}, {}, 255)".format(light, light)
    else:
        return "rgb(255, 127, 127)"
