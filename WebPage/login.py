from passlib.context import CryptContext
import os
import json

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
)

def _encrypt_password(password):
    return pwd_context.hash(password)
    
def login(username, password):
    nodata = True
    if os.path.exists("userdata.txt"):
        with open('users.json', 'r') as ur:
            cf = json.load(ur)
            userdata = []
            if len(cf) > 0:
                for ce in cf.values():
                    userdata.append(ce[0] + "," + ce[1])
            else:
                nodata = False
    else:
        return None
    
    if not nodata:
        return None
    
    for userdata_entry in userdata:
        if pwd_context.verify(username, userdata_entry.split(",")[0]):
            if pwd_context.verify(password, userdata_entry.split(",")[1]):
                return username

def check_user(username):
    nodata = True
    if os.path.exists("userdata.txt"):
        with open('users.json', 'r') as ur:
            cf = json.load(ur)
            userdata = []
            if len(cf) > 0:
                for ce in cf.values():
                    userdata.append(ce[0] + "," + ce[1])
            else:
                nodata = False
                
        #with open("userdata.txt", "r") as userdatafile:
        #    userdata = userdatafile.read().split("|")[:-1]
        #    if userdata == []:
        #        nodata = False
    else:
        return None
    
    if not nodata:
        return None
    
    for userdata_entry in userdata:
        #userdata_entry = bytes(userdata_entry, "utf-8")
        if pwd_context.verify(username, userdata_entry.split(",")[0]):
            return username

def register(username, password):
    if check_user(str(username)) is not None:
        return "user_exists"
    with open('users.json', 'r') as ur:
        cf = json.load(ur)
    newp = _encrypt_password(username)
    print(newp)
    cf.update({newp: [newp,_encrypt_password(password)]})
    with open('users.json', 'w') as uf:
        json.dump(cf, uf)
    #with open("userdata.txt", "w") as userdatafile:
    #    userdatafile.write(bytes(_encrypt_password(username) + "," + _encrypt_password(password) + "|", "utf-8"))
