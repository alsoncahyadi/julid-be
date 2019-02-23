from trello.base import TrelloBase
from trello.trelloclient import TrelloClient
from trello.board import Board
from trello.trellolist import List
from trello.label import Label

from . import enums as e

trello_client = TrelloClient(
    api_key='8c38f7619e8c0dbd0af427a6f145538f',
    api_secret='01d89258fa41a284468d9983eaec2a1f',
    token='46a437ceea33ce9c130d9ad4aea6bda1b7262225be966a858753d26f50bf4a8a',
    token_secret='1af4d3041e6caa4165cfe1bace2115749db8d060d7e9dd67218a9e9667d0f8c3'
)

board = Board(client=trello_client, board_id=e.Board.INSTAGRAM.value)



list_complaints = List(board=board, list_id=e.List.COMPLAINTS.value)
list_on_progress = List(board=board, list_id=e.List.ON_PROGRESS.value)
list_done = List(board=board, list_id=e.List.DONE.value)


labels = {
	'transaksi': Label(trello_client, e.Label.TRANSAKSI.value, 'Transaksi'),
	'product': Label(trello_client, e.Label.PRODUCT.value, 'Product'),
	'pengiriman': Label(trello_client, e.Label.PENGIRIMAN.value, 'Pengiriman'),
	'service': Label(trello_client, e.Label.SERVICE.value, 'Service'),
	'pertanyaan': Label(trello_client, e.Label.PERTANYAAN.value, 'Pertanyaan'),
	'misuh': Label(trello_client, e.Label.MISUH.value, 'Misuh'),
	'lainnya': Label(trello_client, e.Label.LAINNYA.value, 'Lainnya')
}

from julid import settings as s
mongo_db = s.mongo_db
mongo_logs = s.mongo_logs