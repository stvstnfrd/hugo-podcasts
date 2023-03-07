"""
Wrap calls to pandoc for document conversion
"""
import pandoc
import pandoc.types


AttrHolder = (
    # pylint: disable=no-member
    pandoc.types.Code,
    pandoc.types.Link,
    pandoc.types.Image,
    pandoc.types.Span,
    pandoc.types.Div,
    pandoc.types.CodeBlock,
    pandoc.types.Header,
    pandoc.types.Table,
    pandoc.types.Div,
    # pylint: disable=no-member
)
FORMAT_OUTPUT = 'markdown+autolink_bare_uris+smart-fenced_divs-bracketed_spans-escaped_line_breaks'


def normalize_markup(text):
    """
    Normalize HTML/Markdown text into basic Markdown

    RSS feeds could be HTML for plaintext.
    """
    text = text or ''
    text = text.strip()
    format_input = 'markdown+autolink_bare_uris-native_divs-native_spans'
    if '<' in text:
        format_input = 'html-native_divs-native_spans'
    format_output = FORMAT_OUTPUT
    document = pandoc.read(text, format=format_input)
    strip_attributes(document)
    text = pandoc.write(document, format=format_output)
    return text


def strip_attributes(document):
    """
    Remove all HTML attributes from documents
    """
    locations = []
    for element, path in pandoc.iter(document, path=True):
        if isinstance(element, AttrHolder):
            holder, index = path[-1]
            locations.append((element, holder, index))
    # Perform the change in reverse document order
    # not to invalidate the remaining matches.
    for element, holder, index in reversed(locations):
        # pylint: disable=no-member
        attr_index = 0 if not isinstance(element, pandoc.types.Header) else 1
        # pylint: enable=no-member
        attr = ("", [], [])
        holder[index][attr_index] = attr
    return document
