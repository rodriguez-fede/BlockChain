# -*- coding: utf-8 -*-
"""
Created on Fri Nov  5 10:05:13 2021

@author: Fede
"""

from hashlib import sha256
import json
import time


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = []
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        
    # hacer bloques inmutables 
    
    def compute_hash(self):
        """
        
        funcion que crea el hash del bloque
        string_object = json.dumps(block, sort_keys=True) 
        #takes our new block and changes its key/value pairs all into strings
        block_string = string_object.encode()
        #  turns that string into Unicode
        #, which we pass into our SHA256 method from hashlib
        raw_hash = hashlib.sha256(block_string)
        hex_hash = raw_hash.hexdigest() #we create a hexidecimal string from its return value
        
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()
    
class Blockchain:
    
    difdiculty = 2 # dificultad del algoritmo de prueba de trabajo
    
    def __init__(self):
        self.unconfirmed_transactions = [] # info a insterar en blockchain
        self.chain = []
        self.create_genesis_block = ()
        
    def create_genesis_block(self):
        """
        Una función para generar el bloque génesis y añadirlo a la
        cadena. El bloque tiene index 0, previous_hash 0 y un hash
        válido.
        """
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)
        
    @property
    def last_block(self):
        return self.chain[-1]
    
    
    def proof_of_work(self, block):
        """
       Función que intenta distintos valores de nonce hasta obtener
       un hash que satisfaga nuestro criterio de dificultad.
       Agreguemos una condición que nuestro hash deba empezar con dos ceros
       Un nonce es un número que cambiará constantemente hasta que obtengamos
       un hash que satisfaga nuestra condición. 
       El número de ceros prefijados (el valor 2, en nuestro caso) decide la «dificultad»
       prueba de trabajo es difícil de calcular pero fácil de verificar
       una vez que averiguamos el nonce 
       (para verificar, simplemente tienes que ejecutar la función hash nuevamente).

        """
        block.nonce = 0
        
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difdiculty):
            block.nonce += 1
            computed_hash = block.compute_hash()
            
        return computed_hash
    
    
    def add_block(self, block, proof):
        """
       Agrego un block a la cadena que este verificado

        """
        previous_hash = self.last_block.hash
        
        if previous_hash != block.previous_hash:
            return False
        
        if not self.is_valid_proof(block, proof):
            return False
        
        block.hash = proof
        self.chain.append(block)
        return True
    
    def is_valid_proof(self, block, block_hash):
        """
        Chequear si block_hash es un valido y satisface nuestro
        criterio de dificultad

        """
        return (block_hash.startswith('0' * Blockchain.difdiculty) and block_hash == block.compute_hash())
    
    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)
        
    def mine(self):
        """
        Esta función sirve como una interfaz para añadir las transacciones
        pendientes al blockchain añadiéndolas al bloque y calculando la
        prueba de trabajo.

        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []
        return new_block.index
    
    
# Ahora creo interfaces para relacionar nuestro nodo
# utilizando Flask para crear una REST-API que interactúe con nuestro nodo

from flask import Flask, request
import requests

app = Flask(__name__)

# copio la clase en otra variable, es decir copio el nodo del Blockchain
blockchain = Blockchain()

"""
Necesitamos un punto de acceso para nuestra aplicación 
para enviar una nueva transacción.
 Éste será utilizado por nuestra aplicación
 para añadir nueva información (publicaciones) al blockchain:
"""
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["author", "content"]
 
    for field in required_fields:
        if not tx_data.get(field):
            return "Invlaid transaction data", 404
 
    tx_data["timestamp"] = time.time()
 
    blockchain.add_new_transaction(tx_data)
 
    return "Success", 201

"""
Aquí hay un punto de acceso para retornar la copia del blockchain que tiene el nodo.
 Nuestra aplicación estará usando este punto de acceso para solicitar 
 todas las publicaciones para mostrar.
"""

@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data})

"""
Y aquí hay otro para solicitar al nodo que mine las transacciones sin confirmar 
(si es que hay alguna).
"""

@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    return "Block #{} is mined.".format(result)
 
 
# punto de acceso para obtener las transacciones
# no confirmadas
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)
 
 
app.run(debug=True, port=8000)
        
        
# Establecer consenso y descentralización
# hasta ahora esta pensado para ser ejecutado en una sola pc
# necesitasmos multiples nodos
# por lo tanto creemos un punto de acceso para permitirle a un nodo 
# tener conciencia de otros compañeros en la red

# la dirección de otros miembros que participan en la red
peers = set()
 
# punto de acceso para añadir nuevos compañeros a la red.
@app.route('/add_nodes', methods=['POST'])
def register_new_peers():
    nodes = request.get_json()
    if not nodes:
        return "Invalid data", 400
    for node in nodes:
        peers.add(node)
 
    return "Success", 201

# para mantener la integridad de todo el sistema. Necesitamos consensuar.
# ya que  la copia de cadenas de algunos nodos puede diferir

#Un algoritmo simple de consenso podría ser 
#ponernos de acuerdo respecto de la cadena válida más larga
#cuando las cadenas de diferentes participantes de la red aparentan divergir.
#La racionalidad debajo de este procedimiento es
#que la cadena más larga es una buena estimación de la mayor cantidad de trabajo realizado:

def consensus():
    """
    Nuestro simple algoritmo de consenso. Si una cadena válida más larga es
    encontrada, la nuestra es reemplazada por ella.
    """
    global blockchain
 
    longest_chain = None
    current_len = len(blockchain)
 
    for node in peers:
        response = requests.get('http://{}/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain
 
    if longest_chain:
        blockchain = longest_chain
        return True
 
    return False

#necesitamos desarrollar una forma para que cada nodo pueda anunciar
#a la red que ha minado un bloque para que todos puedan actualizar su blockchain 
#y seguir minando otras transacciones.
#Otros nodos pueden simplemente verificar la prueba de trabajo y 
#añadirla a sus respectivas cadenas

# punto de acceso para añadir un bloque minado por alguien más a la cadena del nodo.
@app.route('/add_block', methods=['POST'])
def validate_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"], block_data["transactions"],
                  block_data["timestamp", block_data["previous_hash"]])
 
    proof = block_data['hash']
    added = blockchain.add_block(block, proof)
 
    if not added:
        return "The block was discarded by the node", 400
 
    return "Block added to the chain", 201
def announce_new_block(block):
    for peer in peers:
        url = "http://{}/add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))
        #El método announce_new_block debería ser llamado luego que
        #un bloque ha sido minado por el nodo,
        #para que los compañeros lo puedan añadir a sus cadenas


