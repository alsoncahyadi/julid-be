from enum import Enum

# To access id: <Enum>.<Constant>.value
# example: Board.INSTAGRAM.value
# best practicenya di environment variable or .env IMO, but for now disini dulu

class Board(Enum):
    INSTAGRAM = '5c63ffc5718fcc189512f3c5' 

class List(Enum):
    COMPLAINTS = '5c63ffe72644363761a1f32d'
    ON_PROGRESS = '5c63ffec35fa7d5c175241ac'
    DONE = '5c63ffee7ce31c3c3f71a3b2'

class Label(Enum):
    TRANSAKSI = "5c65bbc5acf642332d7eeb48"
    PRODUCT = "5c63ffc591d0c2ddc5c4dc1c"
    PENGIRIMAN = "5c63ffc591d0c2ddc5c4dc1b"
    SERVICE = "5c63ffc591d0c2ddc5c4dc1d"
    PERTANYAAN = "5c63ffc591d0c2ddc5c4dc21"
    MISUH = "5c63ffc591d0c2ddc5c4dc2b"
    LAINNYA = "5c63ffc591d0c2ddc5c4dc2a"

class ActionType(Enum):
    UPDATE_CARD = "updateCard"

class TranslationKey(Enum):
    ACTION_MOVE_CARD_FROM_LIST_TO_LIST = 'action_move_card_from_list_to_list'