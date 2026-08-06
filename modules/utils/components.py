def iter_children(message):
    for component in getattr(message, 'components', []) or []:
        yield from _iter_component_children(component)


def _iter_component_children(component):
    children = getattr(component, 'children', None) or getattr(component, 'components', None)
    if not children:
        return
    for child in children:
        yield child
        yield from _iter_component_children(child)


def section_content(section):
    children = getattr(section, 'children', None) or getattr(section, 'components', None)
    if not children:
        return getattr(section, 'content', '') or ''
    parts = [section_content(child) for child in children]
    return '\n'.join(part for part in parts if part)