from jarbas_hive_mind.database import ClientDatabase


# name can be anything, currently not used, meant for humans
name = "NotHuman"
# access key, think of it like a password
key = "erpDerPerrDurHUr"

# pre-shared symmetric encryption key, to end2end encrypt your payloads
# (optional) automated key exchange is WIP and meant to mostly replace this
# None will disable it (default)
crypto_key = None  # NOTE: needs to be 16chars, will be cropped if longer

# currently not used, spoof it
mail = "jarbasai@mailfence.com"


with ClientDatabase() as db:
    db.add_client(name, mail, key, crypto_key=crypto_key)
