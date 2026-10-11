# -*- coding: utf-8 -*-
"""Ghi log có cấu trúc.

Mỗi dòng log là JSON một dòng, có mã request để đối chiếu khi người dùng
báo lỗi. Ở chế độ phát triển thì in thành dòng dễ đọc cho người lập trình.
"""
from __future__ import annotations

import contextvars
import json
import logging
import sys
import time

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('request_id', default='-')
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('user_id', default='-')


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        du_lieu = {
            'ts': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(record.created)),
            'level': record.levelname,
            'logger': record.name,
            'request_id': request_id_var.get(),
            'user_id': user_id_var.get(),
            'msg': record.getMessage(),
        }
        if record.exc_info:
            du_lieu['exc'] = self.formatException(record.exc_info)[-2000:]
        for k, v in (getattr(record, 'extra_fields', None) or {}).items():
            du_lieu[k] = v
        return json.dumps(du_lieu, ensure_ascii=False)


class _HumanFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rid = request_id_var.get()
        dau = '' if rid == '-' else '[%s] ' % rid
        dong = '%s%s- %s' % (dau, record.levelname[:1], record.getMessage())
        if record.exc_info:
            dong += '\n' + self.formatException(record.exc_info)
        return dong


def cau_hinh(debug: bool = True) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(_JsonFormatter() if not debug else _HumanFormatter())
    root.addHandler(h)
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    # Thư viện phát ra quá nhiều tin không liên quan.
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('python_multipart').setLevel(logging.WARNING)


def get(name: str) -> logging.Logger:
    return logging.getLogger('garage.' + name)


def log_thong_tap(loi: Exception, nghiep_vu: str, **truong_bo_sung) -> None:
    get('loi').error('Lỗi ở %s: %s', nghiep_vu, loi,
                     extra={'extra_fields': {'nghiep_vu': nghiep_vu, **truong_bo_sung}},
                     exc_info=loi)