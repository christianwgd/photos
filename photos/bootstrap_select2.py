from django import forms
from django_select2.forms import Select2MultipleWidget, ModelSelect2Widget, Select2Widget, ModelSelect2MultipleWidget


class BootstrapSelect2Widget(Select2Widget):
    def build_attrs(self, *args, **kwargs):
        attrs = super(BootstrapSelect2Widget, self).build_attrs(*args, **kwargs)
        attrs.setdefault('data-theme', 'bootstrap')
        return attrs

    @property
    def media(self):
        return super(BootstrapSelect2Widget, self).media + forms.Media(css={
            'screen': ('//cdnjs.cloudflare.com/ajax/libs/select2-bootstrap-theme/'
                       '0.1.0-beta.10/select2-bootstrap.min.css',)})


class BootstrapModelSelect2Widget(ModelSelect2Widget):
    def build_attrs(self, *args, **kwargs):
        attrs = super(BootstrapModelSelect2Widget, self).build_attrs(*args, **kwargs)
        attrs.setdefault('data-theme', 'bootstrap')
        return attrs

    @property
    def media(self):
        return super(BootstrapModelSelect2Widget, self).media + forms.Media(css={
            'screen': ('//cdnjs.cloudflare.com/ajax/libs/select2-bootstrap-theme/'
                       '0.1.0-beta.10/select2-bootstrap.min.css',)})


class BootstrapSelect2MultipleWidget(Select2MultipleWidget):
    def build_attrs(self, *args, **kwargs):
        attrs = super(BootstrapSelect2MultipleWidget, self).build_attrs(*args, **kwargs)
        attrs.setdefault('data-theme', 'bootstrap')
        return attrs

    @property
    def media(self):
        return super(BootstrapSelect2MultipleWidget, self).media + forms.Media(css={
            'screen': ('//cdnjs.cloudflare.com/ajax/libs/select2-bootstrap-theme/'
                       '0.1.0-beta.10/select2-bootstrap.min.css',)})


class BootstrapModelSelect2MultipleWidget(ModelSelect2MultipleWidget):
    def build_attrs(self, *args, **kwargs):
        attrs = super(BootstrapModelSelect2MultipleWidget, self).build_attrs(*args, **kwargs)
        attrs.setdefault('data-theme', 'bootstrap')
        return attrs

    @property
    def media(self):
        return super(BootstrapModelSelect2MultipleWidget, self).media + forms.Media(css={
            'screen': ('//cdnjs.cloudflare.com/ajax/libs/select2-bootstrap-theme/'
                       '0.1.0-beta.10/select2-bootstrap.min.css',)})