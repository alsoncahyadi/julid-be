from trello import TrelloClient
trello_client = TrelloClient(
    api_key='8c38f7619e8c0dbd0af427a6f145538f',
    api_secret='01d89258fa41a284468d9983eaec2a1f',
    token='46a437ceea33ce9c130d9ad4aea6bda1b7262225be966a858753d26f50bf4a8a',
    token_secret='1af4d3041e6caa4165cfe1bace2115749db8d060d7e9dd67218a9e9667d0f8c3'
)

from julid import settings as s
mongo_db = s.mongo_db
mongo_logs = s.mongo_logs