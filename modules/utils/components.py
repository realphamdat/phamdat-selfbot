def iter_children(message):
    for component in message.components:
        children = getattr(component, 'children', None)
        if children:
            for child in children:
                yield child


def section_content(section):
    children = getattr(section, 'children', None)
    if not children:
        return getattr(section, 'content', '')
    return '\n'.join(getattr(c, 'content', '') for c in children if getattr(c, 'content', ''))