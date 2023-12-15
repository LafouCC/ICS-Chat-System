import socket
import time
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64

# use local loop back address by default
CHAT_IP = '127.0.0.1'
CHAT_IP = socket.gethostbyname(socket.gethostname())


CHAT_PORT = 1112
SERVER = (CHAT_IP, CHAT_PORT)

menu = "\n++++ Choose one of the following commands\n \
        who: to find out who else are there\n \
        c _peer_: to connect to the _peer_ and chat\n \
        sc _peer_: to securely chat with the _peer_\n \
        ? _term_: to search your chat logs where _term_ appears\n \
        p _#_: to get number <#> sonnet\n \
        q: to leave the chat system\n\n"

S_OFFLINE   = 0
S_CONNECTED = 1
S_LOGGEDIN  = 2
S_CHATTING  = 3

SIZE_SPEC = 5

CHAT_WAIT = 0.2



PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n\
MIICXAIBAAKBgQCqFctX71JTXU2P4n8Qstrj+aaZXeaIuif1FrQ9MIJhiVf2MhSY\n\
uvehiFqGGR4dTT/tu73DS9n8R8DcrAaj/7MJU6kRf+loZf/YWXC76lqR6ecQAJHP\n\
9UNVIyrDy8wdJvSmoT3Wjwod9zy4y06Uv62iDtfvmfuCetEezED9zVTQFwIDAQAB\n\
AoGAA6rGoJW7W6rGUlTa0nxYtdObIPFiWA5TcDhWGH+kQAAbEmbQBN77GdN7yCpg\n\
eNdCipiipcRL5eGSKe/XkM+hh4fzj6/fPQlV5BsWBgtpebecgM71nig/tG8m52sh\n\
AhvC2qrxvtufE4Jwxz1V54IK5s/nZKpOSej4zDCPNjqkp8ECQQDOAnDd0FvcqLK2\n\
r7lQ0k7lxdx2KBI2a6EqETzbeQ9HO4qAzgi8gIHZvz1+xtao1C1/G/HLytQdL4kP\n\
qES5VFUhAkEA01uvxfvletwMo0YmZLdYBEVcOKBA8LDO0BfLDfW0xxcP1+RV0XZh\n\
ruvgAvJ7m5OMVKJXuQBEsZFuW2oEp3/GNwJAUEK5MGIl+AEtp2ks/OUC4hhFPS99\n\
cQBbyOTwXd17a1gyLN6YnsA+VtRgJA1Zwmrv0s7TVH+QRlKnxpbbN404oQJAMwhg\n\
WJ2JuzCGnKXDf24FgoJ80e9fvr3yMayNCsHY9HlNCgPH9Ntwmpu5avzBe78Ukxrf\n\
s3utGnLTAp+GoCrp4QJBALGPqMPfBkPeBxuGKsBdmoT0vMuiFy+k/4UGqrvPW/78\n\
Ij9iZ3cUnZKOHmyr+ljN0zQbGe4jHFkc/lJLDLzY4J4=\n\
-----END RSA PRIVATE KEY-----".encode()

PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n\
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCqFctX71JTXU2P4n8Qstrj+aaZ\n\
XeaIuif1FrQ9MIJhiVf2MhSYuvehiFqGGR4dTT/tu73DS9n8R8DcrAaj/7MJU6kR\n\
f+loZf/YWXC76lqR6ecQAJHP9UNVIyrDy8wdJvSmoT3Wjwod9zy4y06Uv62iDtfv\n\
mfuCetEezED9zVTQFwIDAQAB\n\
-----END PUBLIC KEY-----".encode()

#generate public-private key pair
key=RSA.generate(1024)
PRIVATE_KEY=key.export_key()
PUBLIC_KEY=key.publickey().export_key()

#print(PUBLIC_KEY.decode())

def myencrypt(msg,peer_public_key,if_private):
    if if_private==1:
        #encrypt my message using my peer's public key
        cipher=PKCS1_OAEP.new(RSA.import_key(peer_public_key))

        #return binary data and binary string
        EN_data=cipher.encrypt(msg.encode())
        EN_string=base64.b64encode(EN_data).decode()
    else:
        EN_string=msg
    return EN_string

def mydecrypt(msg,if_private):
    if if_private==1:
        #decrypt the message sent from peer by suing my private key
        cipher=PKCS1_OAEP.new(RSA.import_key(PRIVATE_KEY))
        received_data=base64.b64decode(msg.encode())
        DE_string=cipher.decrypt(received_data).decode()
    else:
        DE_string=msg
    return DE_string

def print_state(state):
    print('**** State *****::::: ')
    if state == S_OFFLINE:
        print('Offline')
    elif state == S_CONNECTED:
        print('Connected')
    elif state == S_LOGGEDIN:
        print('Logged in')
    elif state == S_CHATTING:
        print('Chatting')
    else:
        print('Error: wrong state')

def mysend(s, msg):
    #append size to message and send it
    #SIZE_SPEC 是表示第一次receive需要receive多少information(这里需要receive5个)
    msg = ('0' * SIZE_SPEC + str(len(msg)))[-SIZE_SPEC:] + str(msg)
    msg = msg.encode()
    total_sent = 0
    while total_sent < len(msg):
        sent = s.send(msg[total_sent:])
        if sent==0:
            print('server disconnected')
            break
        total_sent += sent

def myrecv(s):
    #receive size first
    size = ''
    while len(size) < SIZE_SPEC:
        text = s.recv(SIZE_SPEC - len(size)).decode()
        if not text:
            print('disconnected')
            return('')
        size += text
    size = int(size)
    #now receive message
    msg = ''
    while len(msg) < size:
        text = s.recv(size-len(msg)).decode()
        if text == b'':
            print('disconnected')
            break
        msg += text
    #print ('received '+message)
    return (msg)

def text_proc(text, user):
    ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
    return('(' + ctime + ') ' + user + ' : ' + text) # message goes directly to screen
