def envoi(message = None, embed = None):
    import requests
    WEBHOOK = <WEBHOOK LINK>
    if embed == None:
        r = requests.post(WEBHOOK, json={'content':message})
    else:
        import discord
        r = requests.post(WEBHOOK, json = {'content':message, 'embeds':[embed]})
    if r.status_code != 204:
        return False,f"Echec de l'envoi, code {r.status_code}"
    else:
        return True,f"Log enregistré avec succès"
        

def log(msg="message du log par défaut"):
    if type(msg) == type(("","")) or type(msg) == type(["",""]):   #si l'argument est un tuple ou une liste
        if len(msg) != 2:
            return False,f"L'utilisation d'un tuple ou d'une liste requiert exactement 2 éléments dans l'objet ({len(msg)} fourni{'s'*(len(msg)>2)})"
        if not ((type(msg[0]) == type("") or type(msg[1]) == type("")) and (type(msg[0]) == type({}) or type(msg[1]) == type({}))):
            return False,f"L'objet fourni est invalide: [{type(msg[0])},{type(msg[1])}] fourni, [string, dict] attendu"
        if type(msg[0]) == type(""):
            return envoi(message = msg[0], embed = msg[1])
        else:
            return envoi(message = msg[1], embed = msg[0])
    else:
        if type(msg) == type(""):
            return envoi(message = msg)
        elif type(msg) == type({}):
            return envoi(embed = msg)
        else:
            return False,f"Format incorrect : {type(msg)} fourni, string ou dictionnaire attendu"
