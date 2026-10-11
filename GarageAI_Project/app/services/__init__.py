# -*- coding: utf-8 -*-
"""Tầng nghiệp vụ.

Nguyên tắc:
* Một thao tác nghiệp vụ = **một transaction**. Đọc rồi ghi bắt buộc nằm chung
  `BEGIN IMMEDIATE` (xem `core/db.py`), nếu không sẽ có race condition khiến
  tiền hoặc tồn kho bị sai.
* Giá và tổng tiền **luôn** do backend tính từ danh mục và CSDL, không nhận từ
  giao diện.
* Không ghi đè lịch sử: đơn giá đã chốt trong hạng mục không đổi theo giá
  danh mục; bản ghi đã phát sinh giao dịch thì không xoá vĩnh viễn.
"""