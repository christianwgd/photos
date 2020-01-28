class ReturnToRefererMixin:
    ''' Mixin that returns to referer '''

    def get(self, request, *args, **kwargs):
        if 'HTTP_REFERER' in request.META:
            request.session['caller'] = request.META['HTTP_REFERER']
        else:
            request.session['caller'] = '/'
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        if hasattr(self, 'success_url'):
            if self.success_url:
                return self.success_url
        return self.request.session['caller']

    def get_cancel_url(self):
        return self.request.session['caller']