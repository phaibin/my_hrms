from django import template

register = template.Library()

@register.filter(name='key')
def key(d, key_name):
    return d.get(key_name, '')