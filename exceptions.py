class TemplateException(Exception):
    pass

class TemplateSyntaxError(TemplateException):
    pass

class TemplateParentNotFoundError(TemplateException):
    """The template does not have a parent template"""
