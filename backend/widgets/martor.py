from martor.widgets import AdminMartorWidget as OldAdminMartorWidget, MartorWidget as OldMartorWidget

__all__ = ['MartorWidget', 'AdminMartorWidget']


class MartorWidget(OldMartorWidget):
    class Media:
        css = {
            'all': ('martor/css/martor.bootstrap.min.css', ),
        }
        js = ['martor-mathjax.js']


class AdminMartorWidget(OldAdminMartorWidget):
    class Media:
        css = MartorWidget.Media.css
