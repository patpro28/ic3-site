import six

formats = {}

def registry_contest_format(name):
    def registry_class(contest_format_class):
        assert name not in formats
        formats[name] = contest_format_class
        return contest_format_class
    
    return registry_class

def choices():
    return [(key, value.name) for key, value in sorted(six.iteritems(formats))]