"""
читает текстовый файл и создает файл json
"""
from req import Req


reqs = Req.read_txt('list_requests_test')
Req.create_json(reqs)