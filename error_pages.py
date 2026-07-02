"""Themed error pages with on-screen diagnostics for production tracing."""
import traceback
from datetime import datetime

from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from config import db

# Friendly copy for common HTTP status codes (and a default for anything else).
ERROR_CATALOG = {
    400: {
        'title': 'Bad Request',
        'headline': 'The request could not be understood.',
        'hint': 'Check the form fields or URL parameters and try again.',
        'icon': 'fa-exclamation-circle',
    },
    401: {
        'title': 'Unauthorized',
        'headline': 'You need to sign in first.',
        'hint': 'Please log in and try again.',
        'icon': 'fa-user-lock',
    },
    403: {
        'title': 'Forbidden',
        'headline': 'You do not have permission to view this.',
        'hint': 'If you believe this is wrong, contact the app owner.',
        'icon': 'fa-ban',
    },
    404: {
        'title': 'Page Not Found',
        'headline': 'This page does not exist.',
        'hint': 'The link may be outdated or the URL was typed incorrectly.',
        'icon': 'fa-map-signs',
    },
    405: {
        'title': 'Method Not Allowed',
        'headline': 'This URL does not accept that action.',
        'hint': 'Use GET to open pages and POST to submit forms.',
        'icon': 'fa-hand-paper',
    },
    408: {
        'title': 'Request Timeout',
        'headline': 'The server waited too long for your request.',
        'hint': 'Try again in a moment. PythonAnywhere may be busy.',
        'icon': 'fa-hourglass-half',
    },
    409: {
        'title': 'Conflict',
        'headline': 'The request conflicted with the current state.',
        'hint': 'Refresh the page and retry the action.',
        'icon': 'fa-random',
    },
    410: {
        'title': 'Gone',
        'headline': 'This resource is no longer available.',
        'hint': 'It may have been removed permanently.',
        'icon': 'fa-trash-alt',
    },
    413: {
        'title': 'Payload Too Large',
        'headline': 'The upload or request body is too big.',
        'hint': 'Reduce the size of your submission and try again.',
        'icon': 'fa-weight-hanging',
    },
    414: {
        'title': 'URI Too Long',
        'headline': 'The URL is too long.',
        'hint': 'Shorten filters or search terms in the address bar.',
        'icon': 'fa-link',
    },
    415: {
        'title': 'Unsupported Media Type',
        'headline': 'The server cannot process this file type.',
        'hint': 'Use supported formats only.',
        'icon': 'fa-file-excel',
    },
    422: {
        'title': 'Unprocessable Entity',
        'headline': 'The data was well-formed but invalid.',
        'hint': 'Review the values you submitted.',
        'icon': 'fa-clipboard-check',
    },
    429: {
        'title': 'Too Many Requests',
        'headline': 'You are sending requests too quickly.',
        'hint': 'Wait a few seconds and try again.',
        'icon': 'fa-tachometer-alt',
    },
    500: {
        'title': 'Internal Server Error',
        'headline': 'Something went wrong on the server.',
        'hint': 'Copy the technical details below when reporting this issue.',
        'icon': 'fa-bug',
    },
    501: {
        'title': 'Not Implemented',
        'headline': 'This feature is not available yet.',
        'hint': 'The server does not support this operation.',
        'icon': 'fa-tools',
    },
    502: {
        'title': 'Bad Gateway',
        'headline': 'The server received an invalid upstream response.',
        'hint': 'Try reloading. If it persists, restart the web app on PythonAnywhere.',
        'icon': 'fa-server',
    },
    503: {
        'title': 'Service Unavailable',
        'headline': 'The service is temporarily unavailable.',
        'hint': 'Wait a moment and reload the page.',
        'icon': 'fa-plug',
    },
    504: {
        'title': 'Gateway Timeout',
        'headline': 'The server timed out waiting for a response.',
        'hint': 'Heavy tasks (archive rebuild, backup) may need more time or a retry.',
        'icon': 'fa-clock',
    },
}

DEFAULT_ERROR = {
    'title': 'Unexpected Error',
    'headline': 'An unexpected error occurred.',
    'hint': 'Copy the technical details below for troubleshooting.',
    'icon': 'fa-exclamation-triangle',
}


def _catalog_entry(code):
    return ERROR_CATALOG.get(code, DEFAULT_ERROR)


def _build_context(code, exc=None, exc_type=None, trace_text=None):
    meta = _catalog_entry(code)
    message = ''
    if exc is not None:
        message = str(exc).strip()
    if not message and exc is not None and hasattr(exc, 'description'):
        message = str(exc.description or '').strip()

    return {
        'code': code,
        'title': meta['title'],
        'headline': meta['headline'],
        'hint': meta['hint'],
        'icon': meta['icon'],
        'message': message,
        'exc_type': exc_type or (type(exc).__name__ if exc else ''),
        'trace': trace_text or '',
        'path': request.path,
        'method': request.method,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'query': request.query_string.decode('utf-8', errors='replace') if request.query_string else '',
    }


def _wants_json():
    if request.path.startswith('/api/'):
        return True
    best = request.accept_mimetypes.best
    return (
        best == 'application/json'
        and request.accept_mimetypes[best] >= request.accept_mimetypes['text/html']
    )


def _render_error(code, ctx):
    if _wants_json():
        return jsonify({
            'error': True,
            'code': ctx['code'],
            'title': ctx['title'],
            'message': ctx['message'],
            'exc_type': ctx['exc_type'],
            'trace': ctx['trace'],
            'path': ctx['path'],
            'method': ctx['method'],
            'timestamp': ctx['timestamp'],
        }), code
    return render_template('errors/error.html', **ctx), code


def _rollback_db():
    try:
        db.session.rollback()
    except Exception:
        pass


def handle_http_exception(exc):
    code = exc.code if exc.code is not None else 500
    if code >= 500:
        _rollback_db()
    ctx = _build_context(code, exc=exc)
    return _render_error(code, ctx)


def handle_uncaught_exception(exc):
    _rollback_db()
    trace_text = traceback.format_exc()
    ctx = _build_context(
        500,
        exc=exc,
        exc_type=type(exc).__name__,
        trace_text=trace_text,
    )
    return _render_error(500, ctx)


def register_error_handlers(application):
    @application.errorhandler(HTTPException)
    def _http_error(exc):
        return handle_http_exception(exc)

    @application.errorhandler(Exception)
    def _uncaught_error(exc):
        if isinstance(exc, HTTPException):
            return handle_http_exception(exc)
        return handle_uncaught_exception(exc)
