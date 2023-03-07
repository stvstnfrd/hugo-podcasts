"""
Process Markdown text
"""
import frontmatter
import yaml


class NoAliasDumper(yaml.SafeDumper):
    """
    A YAML-Dumper that removes all YAML-aliases
    """

    def ignore_aliases(self, data):
        """
        Ignore aliases during serialization
        """
        return True


class HugoFeedDocument:
    """
    Represent Hugo-compatible Markdown documents
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, data, is_draft=False):
        self.data = data
        self.is_draft = is_draft

    def __str__(self):
        feed_data = self.data
        use_yaml_lib = True
        hugo_data = {
            'podcast': dict(feed_data),
            'title': feed_data['title'],
            'date': feed_data.get('date') or feed_data.get('pub_date'),
            'draft': self.is_draft,
        }
        if 'tags' in feed_data:
            hugo_data['tags'] = feed_data['tags']
        description = feed_data.get('description') or ''
        if 'podcast' in hugo_data and 'description' in hugo_data['podcast']:
            del hugo_data['podcast']['description']
        # del hugo_data['feed_url']
        document = frontmatter.Post(description, **hugo_data)
        if not use_yaml_lib:
            text = frontmatter.dumps(document)
        else:
            header = yaml.dump(
                {
                    key: value if isinstance(value, str) else value
                    for key, value in document.metadata.items()
                },
                indent=4,
                Dumper=NoAliasDumper,
            )
            text = f"---\n{header}\n---\n\n{description}"
        return text
